"""Data models for Monte Carlo Fund Simulation"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple
import hashlib
import json


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
