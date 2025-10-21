"""Data models for Monte Carlo Fund Simulation"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
import hashlib
import json
import numpy as np


@dataclass
class Investment:
    """
    Represents a historical investment with actual performance data.

    Attributes:
        investment_name: Name of the portfolio company
        fund_name: Name of the fund that made the investment
        entry_date: Date when investment was made
        latest_date: Date of most recent valuation or exit
        moic: Multiple on Invested Capital (e.g., 2.5 = 2.5x return)
        irr: Internal Rate of Return as decimal (e.g., 0.25 = 25%)
    """
    investment_name: str
    fund_name: str
    entry_date: datetime
    latest_date: datetime
    moic: float
    irr: float

    @property
    def days_held(self) -> int:
        """Calculate calendar days between entry and latest date."""
        return (self.latest_date - self.entry_date).days

    def validate(self) -> List[str]:
        """
        Validate investment data integrity.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        if not self.investment_name or not self.investment_name.strip():
            errors.append("Investment name is required")

        if not self.fund_name or not self.fund_name.strip():
            errors.append("Fund name is required")

        if self.entry_date >= self.latest_date:
            errors.append(
                f"Entry date ({self.entry_date.date()}) must be before "
                f"latest date ({self.latest_date.date()})"
            )

        if self.moic < 0:
            errors.append(f"MOIC ({self.moic:.2f}) cannot be negative")

        if self.irr < -1.0:
            errors.append(f"IRR ({self.irr:.2%}) cannot be less than -100%")

        return errors


@dataclass
class SimulationConfiguration:
    """
    Configuration for Monte Carlo simulation.
    All rate parameters are stored as decimals (0.20 = 20%).
    """
    # Fund Information
    fund_name: str = ""
    fund_manager: str = ""

    # Financial Parameters
    leverage_rate: float = 0.0
    cost_of_capital: float = 0.08
    fee_rate: float = 0.02
    carry_rate: float = 0.20
    hurdle_rate: float = 0.08

    # Simulation Parameters
    simulation_count: int = 10000
    investment_count_mean: float = 10.0
    investment_count_std: float = 2.0

    # Simulation Mode
    simulation_mode: str = "past_performance"  # "past_performance" or "deconstructed_performance"

    # Alpha/Beta Parameters (used in deconstructed mode)
    beta_exposure: float = 1.0  # Beta coefficient (β) for geometric attribution
    beta_index_hash: str = ""

    # Beta Forward Simulation Parameters (for deconstructed mode - Constant growth method)
    beta_horizon_days: int = 3650  # 10 years default (trading days)
    beta_n_paths: int = 1000
    beta_outlook: str = "base"  # "pessimistic", "base", or "optimistic"
    beta_confidence: str = "medium"  # "low", "medium", or "high"

    # Deduplication Hashes
    data_hash: str = ""
    total_hash: str = ""

    def validate(self) -> List[str]:
        """Validate configuration parameters."""
        errors = []

        if not self.fund_name or not self.fund_name.strip():
            errors.append("Fund name is required")

        if not self.fund_manager or not self.fund_manager.strip():
            errors.append("Fund manager is required")

        if not (0 <= self.leverage_rate <= 1):
            errors.append(f"Leverage rate must be 0-100% (got {self.leverage_rate:.2%})")

        if not (0 <= self.cost_of_capital <= 1):
            errors.append(f"Cost of capital must be 0-100% (got {self.cost_of_capital:.2%})")

        if not (0 <= self.fee_rate <= 0.1):
            errors.append(f"Management fee rate must be 0-10% (got {self.fee_rate:.2%})")

        if not (0 <= self.carry_rate <= 0.5):
            errors.append(f"Carry rate must be 0-50% (got {self.carry_rate:.2%})")

        if not (0 <= self.hurdle_rate <= 1):
            errors.append(f"Hurdle rate must be 0-100% (got {self.hurdle_rate:.2%})")

        if not (100 <= self.simulation_count <= 1000000):
            errors.append(f"Simulation count must be 100-1,000,000 (got {self.simulation_count})")

        if self.investment_count_mean < 1:
            errors.append(f"Investment count mean must be ≥1 (got {self.investment_count_mean})")

        if self.investment_count_std < 0:
            errors.append(f"Investment count std dev cannot be negative (got {self.investment_count_std})")

        if self.beta_exposure < 0:
            errors.append(f"Beta exposure cannot be negative (got {self.beta_exposure})")

        # Validate simulation mode
        valid_modes = ["past_performance", "deconstructed_performance"]
        if self.simulation_mode not in valid_modes:
            errors.append(f"Invalid simulation mode '{self.simulation_mode}'. Must be one of: {', '.join(valid_modes)}")

        # Validate beta simulation parameters (for deconstructed mode)
        if self.beta_horizon_days < 1:
            errors.append(f"Beta horizon must be at least 1 day (got {self.beta_horizon_days})")

        if not (100 <= self.beta_n_paths <= 100000):
            errors.append(f"Beta paths must be 100-100,000 (got {self.beta_n_paths})")

        valid_outlooks = ["pessimistic", "base", "optimistic"]
        if self.beta_outlook not in valid_outlooks:
            errors.append(f"Beta outlook must be one of: {', '.join(valid_outlooks)} (got {self.beta_outlook})")

        valid_confidence = ["low", "medium", "high"]
        if self.beta_confidence not in valid_confidence:
            errors.append(f"Beta confidence must be one of: {', '.join(valid_confidence)} (got {self.beta_confidence})")

        return errors

    def generate_hash(self, investments: List[Investment]) -> Tuple[str, str]:
        """Generate SHA256 hashes for deduplication."""
        # Data hash: SHA256 of sorted investment data
        investment_data = sorted([
            {
                'name': inv.investment_name,
                'fund': inv.fund_name,
                'entry': inv.entry_date.isoformat(),
                'latest': inv.latest_date.isoformat(),
                'moic': round(inv.moic, 6),
                'irr': round(inv.irr, 6)
            }
            for inv in investments
        ], key=lambda x: (x['name'], x['fund']))

        data_str = json.dumps(investment_data, sort_keys=True)
        self.data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        # Total hash: SHA256 of data hash + configuration
        config_data = {
            'data_hash': self.data_hash,
            'leverage_rate': round(self.leverage_rate, 6),
            'cost_of_capital': round(self.cost_of_capital, 6),
            'fee_rate': round(self.fee_rate, 6),
            'carry_rate': round(self.carry_rate, 6),
            'hurdle_rate': round(self.hurdle_rate, 6),
            'simulation_count': self.simulation_count,
            'investment_count_mean': round(self.investment_count_mean, 6),
            'investment_count_std': round(self.investment_count_std, 6),
            'fund_name': self.fund_name,
            'fund_manager': self.fund_manager
        }

        total_str = json.dumps(config_data, sort_keys=True)
        self.total_hash = hashlib.sha256(total_str.encode()).hexdigest()

        return self.data_hash, self.total_hash


@dataclass
class InvestmentDetail:
    """Details about a single investment within a simulation."""
    investment_name: str
    entry_date: datetime
    exit_date: datetime
    simulated_moic: float
    simulated_irr: float
    alpha_moic: Optional[float] = None  # Alpha MOIC (preserved during reconstruction)
    alpha_irr: Optional[float] = None   # Alpha IRR (preserved during reconstruction)
    beta_moic: Optional[float] = None
    beta_irr: Optional[float] = None
    days_held: int = 0
    investment_amount: float = 1_000_000


@dataclass
class SimulationResult:
    """Result from a single Monte Carlo simulation iteration."""
    simulation_id: int
    investments_selected: List[str]
    investment_count: int
    total_invested: float
    total_returned: float
    moic: float
    irr: float
    gross_profit: float
    net_profit: float
    fees_paid: float
    carry_paid: float
    leverage_cost: float

    # Diagnostic fields for alpha simulations
    has_negative_cash_flows: bool = False
    irr_converged: bool = True
    negative_total_returned: bool = False

    # Detailed tracking (optional, populated when export_details=True)
    investment_details: Optional[List[InvestmentDetail]] = None
    cash_flow_schedule: Optional[Dict[int, float]] = None


@dataclass
class SimulationSummary:
    """Statistical summary of Monte Carlo simulation results."""
    config: SimulationConfiguration
    total_runs: int
    timestamp: datetime

    # MOIC Statistics
    mean_moic: float
    median_moic: float
    std_moic: float
    min_moic: float
    max_moic: float
    percentile_5_moic: float
    percentile_25_moic: float
    percentile_75_moic: float
    percentile_95_moic: float

    # IRR Statistics
    mean_irr: float
    median_irr: float
    std_irr: float
    min_irr: float
    max_irr: float
    percentile_5_irr: float
    percentile_25_irr: float
    percentile_75_irr: float
    percentile_95_irr: float


@dataclass
class BetaPrice:
    """Single beta index price observation."""
    date: datetime
    price: float

    def validate(self) -> List[str]:
        """Validate beta price data."""
        errors = []
        if self.price <= 0:
            errors.append(f"Price must be positive (got {self.price})")
        return errors


@dataclass
class BetaPriceIndex:
    """
    Beta pricing index with linear interpolation between period midpoints.

    Attributes:
        prices: List of beta price observations (must be sorted by date)
        frequency: Data frequency declared by user ("daily", "weekly", "monthly", "quarterly", "annual", "irregular")
        data_hash: SHA256 hash for deduplication
    """
    prices: List[BetaPrice]
    frequency: str
    data_hash: str = ""

    def calculate_midpoint(self, date: datetime) -> datetime:
        """
        Calculate the midpoint of the period based on user-declared frequency.

        Args:
            date: Date from CSV

        Returns:
            Datetime representing midpoint of period
        """
        if self.frequency == "daily":
            return date

        elif self.frequency == "weekly":
            # Assume date is Monday, midpoint is Thursday (+3 days)
            return date + timedelta(days=3)

        elif self.frequency == "monthly":
            # Calculate middle of month
            year, month = date.year, date.month

            # Get last day of month
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)

            last_day = (next_month - timedelta(days=1)).day
            midpoint_day = last_day // 2

            return datetime(year, month, midpoint_day)

        elif self.frequency == "quarterly":
            # Determine quarter
            quarter = (date.month - 1) // 3 + 1

            # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
            quarter_start_month = (quarter - 1) * 3 + 1

            # Calculate midpoint (45 days into quarter)
            quarter_start = datetime(date.year, quarter_start_month, 1)
            midpoint = quarter_start + timedelta(days=45)

            return midpoint

        elif self.frequency == "annual":
            # Midpoint of year (July 2nd)
            return datetime(date.year, 7, 2)

        else:
            # Irregular: use date as-is (no adjustment)
            return date

    def get_price_on_date(self, target_date: datetime) -> float:
        """
        Get beta price for a specific date using linear interpolation.

        Args:
            target_date: Date to get price for

        Returns:
            Interpolated price

        Raises:
            ValueError: If target_date is outside beta data range
        """
        if not self.prices:
            raise ValueError("Beta index has no price data")

        # Convert price dates to midpoints
        midpoints = [(self.calculate_midpoint(p.date), p.price) for p in self.prices]

        # Check coverage
        min_date = midpoints[0][0]
        max_date = midpoints[-1][0]

        if target_date < min_date or target_date > max_date:
            raise ValueError(
                f"Beta data does not cover target date {target_date.date()}. "
                f"Beta range: {min_date.date()} to {max_date.date()}. "
                f"Please upload beta prices covering this entire period."
            )

        # Find surrounding points
        for i in range(len(midpoints) - 1):
            date1, price1 = midpoints[i]
            date2, price2 = midpoints[i + 1]

            if date1 <= target_date <= date2:
                # Linear interpolation
                days_total = (date2 - date1).days
                days_from_start = (target_date - date1).days

                if days_total == 0:
                    return price1

                weight = days_from_start / days_total
                interpolated_price = price1 + (price2 - price1) * weight

                return interpolated_price

        # Exact match on last point
        if target_date == midpoints[-1][0]:
            return midpoints[-1][1]

        # Should never reach here
        raise ValueError(f"Could not interpolate price for {target_date}")

    def calculate_return(self, entry_date: datetime, exit_date: datetime) -> Tuple[float, float]:
        """
        Calculate beta MOIC and IRR over investment period.

        Args:
            entry_date: Investment entry date
            exit_date: Investment exit date

        Returns:
            Tuple of (beta_moic, beta_irr)

        Raises:
            ValueError: If dates are outside beta data range
        """
        # Get prices at entry and exit
        entry_price = self.get_price_on_date(entry_date)
        exit_price = self.get_price_on_date(exit_date)

        # Calculate MOIC
        beta_moic = exit_price / entry_price

        # Calculate IRR
        days_held = (exit_date - entry_date).days
        if days_held <= 0:
            raise ValueError("Exit date must be after entry date")

        years_held = days_held / 365.25  # Using 365.25 for leap year adjustment
        beta_irr = (beta_moic ** (1 / years_held)) - 1

        return beta_moic, beta_irr

    def validate(self) -> List[str]:
        """Validate beta index data integrity."""
        errors = []

        if not self.prices:
            errors.append("Beta index has no price data")
            return errors

        if len(self.prices) < 2:
            errors.append("Beta index must have at least 2 price points for interpolation")

        # Validate each price
        for i, price in enumerate(self.prices):
            price_errors = price.validate()
            for err in price_errors:
                errors.append(f"Price {i+1}: {err}")

        # Check dates are sorted
        for i in range(len(self.prices) - 1):
            if self.prices[i].date >= self.prices[i+1].date:
                errors.append(
                    f"Prices must be sorted by date: "
                    f"{self.prices[i].date.date()} >= {self.prices[i+1].date.date()}"
                )

        # Validate frequency
        valid_frequencies = ["daily", "weekly", "monthly", "quarterly", "annual", "irregular"]
        if self.frequency not in valid_frequencies:
            errors.append(
                f"Invalid frequency '{self.frequency}'. "
                f"Must be one of: {', '.join(valid_frequencies)}"
            )

        return errors

    def generate_hash(self) -> str:
        """Generate SHA256 hash of beta data for deduplication."""
        price_data = sorted([
            {
                'date': p.date.isoformat(),
                'price': round(p.price, 6)
            }
            for p in self.prices
        ], key=lambda x: x['date'])

        data_str = json.dumps({
            'prices': price_data,
            'frequency': self.frequency
        }, sort_keys=True)

        self.data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        return self.data_hash
