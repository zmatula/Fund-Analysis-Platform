# Monte Carlo Fund Simulation - Implementation Blueprint

**Version:** 1.0
**Last Updated:** 2025-10-19
**Target:** Clean Python Implementation

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: Project Setup](#phase-1-project-setup)
3. [Phase 2: Data Models](#phase-2-data-models)
4. [Phase 3: Core Calculators](#phase-3-core-calculators)
5. [Phase 4: Data Import](#phase-4-data-import)
6. [Phase 5: Simulation Engine](#phase-5-simulation-engine)
7. [Phase 6: Statistics & Analysis](#phase-6-statistics--analysis)
8. [Phase 7: User Interface](#phase-7-user-interface)
9. [Phase 8: Testing & Validation](#phase-8-testing--validation)
10. [Phase 9: Deployment](#phase-9-deployment)

---

## Prerequisites

### Required Knowledge
- Python 3.8+
- Basic statistics (mean, median, percentiles)
- Financial concepts (IRR, MOIC, leverage, carried interest)
- NumPy for numerical operations
- Streamlit for web UI (optional)

### Development Environment
```bash
# Python 3.8 or higher
python --version

# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Git (optional but recommended)
git --version
```

### Time Estimate
- **Phase 1-6 (Core Logic):** 8-12 hours
- **Phase 7 (UI):** 4-6 hours
- **Phase 8 (Testing):** 4-8 hours
- **Total:** 16-26 hours for complete implementation

---

## Phase 1: Project Setup

### Step 1.1: Create Project Directory

```bash
mkdir fund_simulation
cd fund_simulation
```

### Step 1.2: Initialize Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Step 1.3: Create Project Structure

```bash
mkdir -p fund_simulation
touch fund_simulation/__init__.py
touch fund_simulation/models.py
touch fund_simulation/calculators.py
touch fund_simulation/data_import.py
touch fund_simulation/simulation.py
touch fund_simulation/statistics.py
touch fund_simulation/visualization.py
touch fund_simulation/utils.py
touch app.py
touch requirements.txt
touch README.md
```

### Step 1.4: Create requirements.txt

```txt
# requirements.txt
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.17.0
python-dateutil>=2.8.2
```

### Step 1.5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 1.6: Verify Installation

```python
# test_imports.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

print("All imports successful!")
```

```bash
python test_imports.py
```

---

## Phase 2: Data Models

### Step 2.1: Create models.py

Create `fund_simulation/models.py` with the following classes:

#### Investment Model

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Investment:
    """
    Represents a historical investment with actual performance data.
    """
    investment_name: str
    fund_name: str
    entry_date: datetime
    latest_date: datetime
    moic: float  # Multiple on Invested Capital
    irr: float   # Internal Rate of Return (decimal)

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
```

#### SimulationConfiguration Model

```python
from dataclasses import dataclass
from typing import List, Tuple
import hashlib
import json

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

    def generate_hash(self, investments: List['Investment']) -> Tuple[str, str]:
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
```

#### SimulationResult and SimulationSummary Models

```python
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
```

### Step 2.2: Test Data Models

Create `tests/test_models.py`:

```python
from fund_simulation.models import Investment, SimulationConfiguration
from datetime import datetime

def test_investment_validation():
    # Valid investment
    inv = Investment(
        investment_name="Test Co",
        fund_name="Fund I",
        entry_date=datetime(2020, 1, 1),
        latest_date=datetime(2023, 1, 1),
        moic=2.5,
        irr=0.35
    )
    errors = inv.validate()
    assert len(errors) == 0, f"Expected no errors, got {errors}"

    # Invalid: entry_date >= latest_date
    inv_bad = Investment(
        investment_name="Test Co",
        fund_name="Fund I",
        entry_date=datetime(2023, 1, 1),
        latest_date=datetime(2020, 1, 1),
        moic=2.5,
        irr=0.35
    )
    errors = inv_bad.validate()
    assert len(errors) > 0
    assert any("before" in err.lower() for err in errors)

    print("✓ Investment validation tests passed")


def test_config_validation():
    # Valid config
    config = SimulationConfiguration(
        fund_name="Test Fund",
        fund_manager="Test Manager",
        simulation_count=1000
    )
    errors = config.validate()
    assert len(errors) == 0, f"Expected no errors, got {errors}"

    # Invalid: simulation_count too low
    config_bad = SimulationConfiguration(
        fund_name="Test Fund",
        fund_manager="Test Manager",
        simulation_count=50  # Too low
    )
    errors = config_bad.validate()
    assert len(errors) > 0
    assert any("100-1,000,000" in err for err in errors)

    print("✓ Configuration validation tests passed")


if __name__ == "__main__":
    test_investment_validation()
    test_config_validation()
    print("\n✓ All model tests passed!")
```

Run tests:
```bash
python -m tests.test_models
```

---

## Phase 3: Core Calculators

### Step 3.1: Create calculators.py

Create `fund_simulation/calculators.py`:

#### Holding Period Calculator

```python
import math
from typing import Dict

def calculate_holding_period(moic: float, irr: float) -> int:
    """
    Calculate holding period in days from MOIC and IRR.

    Formula: days = 365 × ln(MOIC) / ln(1 + IRR)

    Args:
        moic: Multiple on Invested Capital (must be > 0)
        irr: Internal Rate of Return as decimal (must be > -1.0)

    Returns:
        Number of days (minimum 1)
    """
    # Handle edge cases
    if moic <= 0:
        return 365  # Default to 1 year

    if irr == -1.0:
        irr = -0.9999  # Avoid log(0)

    try:
        # Calculate using logarithmic formula
        days = 365 * math.log(moic) / math.log(1 + irr)
        days = round(days)
        days = max(1, days)  # At least 1 day
        return days
    except (ValueError, ZeroDivisionError):
        # If calculation fails, default to 365 days
        return 365
```

#### IRR Calculator (Newton-Raphson)

```python
def calculate_irr(cash_flows: Dict[int, float], initial_investment: float,
                  max_iterations: int = 100, tolerance: float = 1e-6) -> float:
    """
    Calculate IRR using Newton-Raphson method.

    Args:
        cash_flows: Dictionary mapping day → cash flow amount
        initial_investment: Initial investment (positive number)
        max_iterations: Maximum iterations for convergence
        tolerance: Convergence tolerance

    Returns:
        IRR as decimal (e.g., 0.25 for 25%)
    """
    rate = 0.1  # Initial guess (10%)

    for iteration in range(max_iterations):
        # Calculate NPV and derivative
        npv = -initial_investment
        dnpv = 0.0

        for day, cash_flow in cash_flows.items():
            years = day / 365.0
            discount_factor = (1 + rate) ** years

            # NPV contribution
            npv += cash_flow / discount_factor

            # Derivative contribution
            dnpv -= years * cash_flow / (discount_factor * (1 + rate))

        # Check convergence
        if abs(npv) < tolerance:
            return rate

        # Avoid division by zero
        if dnpv == 0:
            break

        # Newton-Raphson update
        rate = rate - npv / dnpv

        # Bound the rate to reasonable range
        rate = max(-0.9999, min(rate, 10.0))

    # Return best estimate even if not converged
    return rate
```

#### MOIC Calculator

```python
def calculate_moic(total_returned: float, total_invested: float) -> float:
    """
    Calculate Multiple on Invested Capital.

    Args:
        total_returned: Total cash returned
        total_invested: Total cash invested

    Returns:
        MOIC (e.g., 2.5 for 2.5x return)
    """
    if total_invested <= 0:
        return 0.0
    return total_returned / total_invested
```

### Step 3.2: Test Core Calculators

Create `tests/test_calculators.py`:

```python
from fund_simulation.calculators import (
    calculate_holding_period,
    calculate_irr,
    calculate_moic
)

def test_holding_period():
    # Test normal case
    days = calculate_holding_period(moic=2.0, irr=0.25)
    assert 1100 <= days <= 1200, f"Expected ~1134 days, got {days}"

    # Test edge case: MOIC = 0
    days = calculate_holding_period(moic=0, irr=0.25)
    assert days == 365

    # Test edge case: IRR = -1.0
    days = calculate_holding_period(moic=2.0, irr=-1.0)
    assert days >= 1

    print("✓ Holding period tests passed")


def test_irr_calculation():
    # Simple case: $1M invested, $1.5M returned after 2 years
    cash_flows = {730: 1_500_000}
    irr = calculate_irr(cash_flows, 1_000_000)
    # Expected IRR ≈ 22.47%
    assert 0.20 <= irr <= 0.25, f"Expected IRR ~0.2247, got {irr:.4f}"

    print("✓ IRR calculation tests passed")


def test_moic_calculation():
    moic = calculate_moic(2_500_000, 1_000_000)
    assert abs(moic - 2.5) < 0.01, f"Expected 2.5, got {moic}"

    # Edge case: zero investment
    moic = calculate_moic(1_000_000, 0)
    assert moic == 0.0

    print("✓ MOIC calculation tests passed")


if __name__ == "__main__":
    test_holding_period()
    test_irr_calculation()
    test_moic_calculation()
    print("\n✓ All calculator tests passed!")
```

---

## Phase 4: Data Import

### Step 4.1: Create data_import.py

Create `fund_simulation/data_import.py`:

```python
import csv
from datetime import datetime
from typing import List, Tuple
from dateutil import parser as date_parser

from .models import Investment


def parse_csv_file(file_path: str) -> Tuple[List[Investment], List[str]]:
    """
    Parse CSV file and return list of Investment objects.

    CSV Format (NO headers):
    investment_name, fund_name, entry_date, latest_date, MOIC, IRR

    Args:
        file_path: Path to CSV file

    Returns:
        Tuple of (investments, errors)
    """
    investments = []
    errors = []
    seen_combinations = set()

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)

        for row_num, row in enumerate(reader, start=1):
            # Skip empty rows
            if not row or all(cell.strip() == '' for cell in row):
                continue

            # Validate column count
            if len(row) != 6:
                errors.append(
                    f"Row {row_num}: Expected 6 columns, found {len(row)}"
                )
                continue

            try:
                # Parse fields
                investment_name = row[0].strip()
                fund_name = row[1].strip()
                entry_date_str = row[2].strip()
                latest_date_str = row[3].strip()
                moic_str = row[4].strip()
                irr_str = row[5].strip()

                # Validate non-empty
                if not investment_name:
                    errors.append(f"Row {row_num}: Investment name is required")
                    continue

                if not fund_name:
                    errors.append(f"Row {row_num}: Fund name is required")
                    continue

                # Parse dates
                try:
                    entry_date = date_parser.parse(entry_date_str)
                except Exception as e:
                    errors.append(
                        f"Row {row_num}: Invalid entry date '{entry_date_str}'"
                    )
                    continue

                try:
                    latest_date = date_parser.parse(latest_date_str)
                except Exception as e:
                    errors.append(
                        f"Row {row_num}: Invalid latest date '{latest_date_str}'"
                    )
                    continue

                # Parse MOIC
                try:
                    moic = float(moic_str)
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid MOIC '{moic_str}'")
                    continue

                # Parse IRR
                try:
                    irr = float(irr_str)
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid IRR '{irr_str}'")
                    continue

                # Adjust IRR = -1.0 edge case
                if irr == -1.0:
                    irr = -0.9999

                # Create Investment object
                investment = Investment(
                    investment_name=investment_name,
                    fund_name=fund_name,
                    entry_date=entry_date,
                    latest_date=latest_date,
                    moic=moic,
                    irr=irr
                )

                # Validate
                validation_errors = investment.validate()
                if validation_errors:
                    for err in validation_errors:
                        errors.append(f"Row {row_num}: {err}")
                    continue

                # Check for duplicates
                combo = (investment_name, fund_name)
                if combo in seen_combinations:
                    errors.append(
                        f"Row {row_num}: Duplicate investment '{investment_name}' "
                        f"in fund '{fund_name}'"
                    )
                    # Still add it, but warn
                seen_combinations.add(combo)

                investments.append(investment)

            except Exception as e:
                errors.append(f"Row {row_num}: Unexpected error: {str(e)}")
                continue

    return investments, errors
```

### Step 4.2: Test Data Import

Create sample CSV file `tests/sample_data.csv`:

```csv
Test Investment 1,Fund I,2020-01-01,2023-01-01,2.5,0.35
Test Investment 2,Fund I,2019-06-15,2022-12-31,1.8,0.22
Test Investment 3,Fund II,2021-03-10,2024-03-10,3.2,0.45
```

Create `tests/test_data_import.py`:

```python
from fund_simulation.data_import import parse_csv_file

def test_csv_parsing():
    investments, errors = parse_csv_file('tests/sample_data.csv')

    assert len(investments) == 3, f"Expected 3 investments, got {len(investments)}"
    assert len(errors) == 0, f"Expected no errors, got {errors}"

    # Check first investment
    inv = investments[0]
    assert inv.investment_name == "Test Investment 1"
    assert inv.fund_name == "Fund I"
    assert inv.moic == 2.5
    assert inv.irr == 0.35

    print("✓ CSV parsing tests passed")


if __name__ == "__main__":
    test_csv_parsing()
    print("\n✓ All data import tests passed!")
```

---

## Phase 5: Simulation Engine

### Step 5.1: Create simulation.py

Create `fund_simulation/simulation.py`:

```python
import numpy as np
from typing import List, Callable, Optional, Dict

from .models import Investment, SimulationConfiguration, SimulationResult
from .calculators import calculate_holding_period, calculate_irr, calculate_moic


def run_monte_carlo_simulation(
    investments: List[Investment],
    config: SimulationConfiguration,
    progress_callback: Optional[Callable[[float], None]] = None
) -> List[SimulationResult]:
    """
    Run complete Monte Carlo simulation.

    Args:
        investments: List of historical investments
        config: Simulation configuration
        progress_callback: Optional callback for progress updates

    Returns:
        List of simulation results
    """
    # Initialize random state with fixed seed for reproducibility
    random_state = np.random.RandomState(seed=42)

    results = []

    for i in range(config.simulation_count):
        # Run single simulation
        result = run_single_simulation(
            investments, config, i, random_state
        )
        results.append(result)

        # Report progress every 100 simulations
        if progress_callback and (i + 1) % 100 == 0:
            progress_callback((i + 1) / config.simulation_count)

    return results


def run_single_simulation(
    investments: List[Investment],
    config: SimulationConfiguration,
    simulation_id: int,
    random_state: np.random.RandomState
) -> SimulationResult:
    """
    Run a single Monte Carlo simulation iteration.

    Args:
        investments: Available investment universe
        config: Simulation configuration
        simulation_id: ID for this simulation
        random_state: NumPy random state

    Returns:
        SimulationResult object
    """
    # Step 1: Generate portfolio size
    portfolio_size = generate_portfolio_size(
        config.investment_count_mean,
        config.investment_count_std,
        len(investments),
        random_state
    )

    # Step 2: Select investments WITH REPLACEMENT
    selected_investments = select_investments(
        investments, portfolio_size, random_state
    )

    # Step 3: Build cash flow schedule
    cash_flows: Dict[int, float] = {}
    total_invested = 0.0

    for investment in selected_investments:
        # Calculate holding period
        days_held = calculate_holding_period(investment.moic, investment.irr)

        # Investment amount: $1M per position
        investment_amount = 1_000_000
        total_invested += investment_amount

        # Exit cash flow
        exit_amount = investment_amount * investment.moic

        # Aggregate cash flows by day
        if days_held in cash_flows:
            cash_flows[days_held] += exit_amount
        else:
            cash_flows[days_held] = exit_amount

    # Step 4: Calculate total capital (with leverage)
    leverage_amount = total_invested * config.leverage_rate
    total_capital = total_invested + leverage_amount

    # Step 5: Calculate time period
    max_day = max(cash_flows.keys()) if cash_flows else 365
    years_held = max_day / 365.0

    # Step 6: Calculate gross returns
    total_returned = sum(cash_flows.values())
    gross_profit = total_returned - total_capital

    # Step 7: Calculate financial engineering costs
    leverage_cost = leverage_amount * config.cost_of_capital * years_held
    management_fees = total_capital * config.fee_rate * years_held

    # Step 8: Calculate carry
    hurdle_return = total_capital * (1 + config.hurdle_rate * years_held)
    excess_return = max(0, total_returned - hurdle_return)
    carry_paid = excess_return * config.carry_rate

    # Step 9: Calculate net returns to LPs
    net_returned = total_returned - leverage_cost - management_fees - carry_paid
    net_profit = net_returned - total_invested
    net_moic = calculate_moic(net_returned, total_invested)

    # Step 10: Calculate net IRR
    reduction_factor = (net_returned / total_returned) if total_returned > 0 else 0
    net_cash_flows = {day: cf * reduction_factor for day, cf in cash_flows.items()}
    net_irr = calculate_irr(net_cash_flows, total_invested)

    # Step 11: Create result object
    return SimulationResult(
        simulation_id=simulation_id,
        investments_selected=[inv.investment_name for inv in selected_investments],
        investment_count=len(selected_investments),
        total_invested=total_invested,
        total_returned=net_returned,
        moic=net_moic,
        irr=net_irr,
        gross_profit=gross_profit,
        net_profit=net_profit,
        fees_paid=management_fees,
        carry_paid=carry_paid,
        leverage_cost=leverage_cost
    )


def generate_portfolio_size(
    mean: float,
    std_dev: float,
    max_investments: int,
    random_state: np.random.RandomState
) -> int:
    """
    Generate portfolio size from normal distribution.

    Args:
        mean: Mean number of investments
        std_dev: Standard deviation
        max_investments: Maximum possible value
        random_state: NumPy random state

    Returns:
        Integer portfolio size bounded [1, 2 × max_investments]
    """
    # Sample from normal distribution
    size = random_state.normal(loc=mean, scale=std_dev)

    # Round to nearest integer
    size = round(size)

    # Apply bounds
    size = max(1, size)
    size = min(size, max_investments * 2)

    return size


def select_investments(
    investments: List[Investment],
    count: int,
    random_state: np.random.RandomState
) -> List[Investment]:
    """
    Randomly select investments WITH REPLACEMENT.

    Args:
        investments: Available investment universe
        count: Number of investments to select
        random_state: NumPy random state

    Returns:
        List of selected investments (may contain duplicates)
    """
    indices = random_state.choice(len(investments), size=count, replace=True)
    return [investments[i] for i in indices]
```

---

## Phase 6: Statistics & Analysis

### Step 6.1: Create statistics.py

Create `fund_simulation/statistics.py`:

```python
import numpy as np
from datetime import datetime
from typing import List

from .models import SimulationResult, SimulationSummary, SimulationConfiguration


def calculate_summary_statistics(
    results: List[SimulationResult],
    config: SimulationConfiguration
) -> SimulationSummary:
    """
    Calculate summary statistics from simulation results.

    Args:
        results: List of simulation results
        config: Configuration used for simulation

    Returns:
        SimulationSummary object with all statistics
    """
    # Extract MOIC and IRR arrays
    moics = np.array([r.moic for r in results])
    irrs = np.array([r.irr for r in results])

    # Calculate MOIC statistics
    mean_moic = float(np.mean(moics))
    median_moic = float(np.median(moics))
    std_moic = float(np.std(moics))
    min_moic = float(np.min(moics))
    max_moic = float(np.max(moics))
    p5_moic = float(np.percentile(moics, 5))
    p25_moic = float(np.percentile(moics, 25))
    p75_moic = float(np.percentile(moics, 75))
    p95_moic = float(np.percentile(moics, 95))

    # Calculate IRR statistics
    mean_irr = float(np.mean(irrs))
    median_irr = float(np.median(irrs))
    std_irr = float(np.std(irrs))
    min_irr = float(np.min(irrs))
    max_irr = float(np.max(irrs))
    p5_irr = float(np.percentile(irrs, 5))
    p25_irr = float(np.percentile(irrs, 25))
    p75_irr = float(np.percentile(irrs, 75))
    p95_irr = float(np.percentile(irrs, 95))

    return SimulationSummary(
        config=config,
        total_runs=len(results),
        timestamp=datetime.now(),
        mean_moic=mean_moic,
        median_moic=median_moic,
        std_moic=std_moic,
        min_moic=min_moic,
        max_moic=max_moic,
        percentile_5_moic=p5_moic,
        percentile_25_moic=p25_moic,
        percentile_75_moic=p75_moic,
        percentile_95_moic=p95_moic,
        mean_irr=mean_irr,
        median_irr=median_irr,
        std_irr=std_irr,
        min_irr=min_irr,
        max_irr=max_irr,
        percentile_5_irr=p5_irr,
        percentile_25_irr=p25_irr,
        percentile_75_irr=p75_irr,
        percentile_95_irr=p95_irr
    )
```

---

## Phase 7: User Interface (Streamlit)

### Step 7.1: Create app.py

Create `app.py`:

```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Optional

from fund_simulation.data_import import parse_csv_file
from fund_simulation.models import SimulationConfiguration
from fund_simulation.simulation import run_monte_carlo_simulation
from fund_simulation.statistics import calculate_summary_statistics


def main():
    st.set_page_config(
        page_title="Monte Carlo Fund Simulation",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Monte Carlo Fund Simulation")
    st.markdown("Simulate future fund performance using historical investment data")

    # Initialize session state
    if 'investments' not in st.session_state:
        st.session_state.investments = None
    if 'config' not in st.session_state:
        st.session_state.config = None
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'summary' not in st.session_state:
        st.session_state.summary = None

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Data Import",
        "⚙️ Configuration",
        "▶️ Run Simulation",
        "📈 Results"
    ])

    with tab1:
        render_data_import()

    with tab2:
        render_configuration()

    with tab3:
        render_run_simulation()

    with tab4:
        render_results()


def render_data_import():
    st.header("Import Historical Investment Data")

    uploaded_file = st.file_uploader(
        "Upload CSV file (no headers)",
        type=['csv'],
        help="CSV format: investment_name, fund_name, entry_date, latest_date, MOIC, IRR"
    )

    if uploaded_file is not None:
        # Save uploaded file temporarily
        with open("temp_upload.csv", "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Parse CSV
        investments, errors = parse_csv_file("temp_upload.csv")

        if errors:
            st.error("Errors found during import:")
            for error in errors:
                st.error(f"- {error}")

        if investments:
            st.success(f"✓ Successfully loaded {len(investments)} investments")

            # Display data
            df = pd.DataFrame([
                {
                    'Investment': inv.investment_name,
                    'Fund': inv.fund_name,
                    'Entry Date': inv.entry_date.date(),
                    'Latest Date': inv.latest_date.date(),
                    'MOIC': f"{inv.moic:.2f}x",
                    'IRR': f"{inv.irr:.2%}"
                }
                for inv in investments
            ])
            st.dataframe(df, use_container_width=True)

            # Store in session state
            st.session_state.investments = investments


def render_configuration():
    st.header("Configure Simulation Parameters")

    if st.session_state.investments is None:
        st.warning("⚠️ Please import data first")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fund Information")
        fund_name = st.text_input("Fund Name", value="Simulated Fund")
        fund_manager = st.text_input("Fund Manager", value="")

        st.subheader("Financial Parameters")
        leverage_rate = st.slider("Leverage Rate", 0.0, 1.0, 0.0, 0.01,
                                  format="%.0f%%", help="Leverage as % of LP capital") / 100
        cost_of_capital = st.slider("Cost of Capital", 0.0, 1.0, 0.08, 0.01,
                                    format="%.0f%%") / 100
        fee_rate = st.slider("Management Fee Rate", 0.0, 0.10, 0.02, 0.001,
                            format="%.1f%%") / 100
        carry_rate = st.slider("Carry Rate", 0.0, 0.50, 0.20, 0.01,
                              format="%.0f%%") / 100
        hurdle_rate = st.slider("Hurdle Rate", 0.0, 1.0, 0.08, 0.01,
                               format="%.0f%%") / 100

    with col2:
        st.subheader("Simulation Parameters")
        simulation_count = st.number_input(
            "Number of Simulations",
            min_value=100,
            max_value=1000000,
            value=10000,
            step=1000
        )
        investment_count_mean = st.number_input(
            "Portfolio Size (Mean)",
            min_value=1.0,
            value=10.0,
            step=1.0
        )
        investment_count_std = st.number_input(
            "Portfolio Size (Std Dev)",
            min_value=0.0,
            value=2.0,
            step=0.5
        )

    # Create configuration
    config = SimulationConfiguration(
        fund_name=fund_name,
        fund_manager=fund_manager,
        leverage_rate=leverage_rate,
        cost_of_capital=cost_of_capital,
        fee_rate=fee_rate,
        carry_rate=carry_rate,
        hurdle_rate=hurdle_rate,
        simulation_count=int(simulation_count),
        investment_count_mean=investment_count_mean,
        investment_count_std=investment_count_std
    )

    # Validate
    errors = config.validate()
    if errors:
        st.error("Configuration errors:")
        for error in errors:
            st.error(f"- {error}")
    else:
        st.success("✓ Configuration is valid")
        st.session_state.config = config


def render_run_simulation():
    st.header("Run Monte Carlo Simulation")

    if st.session_state.investments is None:
        st.warning("⚠️ Please import data first")
        return

    if st.session_state.config is None:
        st.warning("⚠️ Please configure simulation parameters")
        return

    config = st.session_state.config
    investments = st.session_state.investments

    st.info(f"Ready to run {config.simulation_count:,} simulations with {len(investments)} investments")

    if st.button("▶️ Run Simulation", type="primary"):
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(fraction):
            progress_bar.progress(fraction)
            status_text.text(f"Progress: {fraction*100:.1f}%")

        # Run simulation
        with st.spinner("Running simulation..."):
            results = run_monte_carlo_simulation(
                investments,
                config,
                progress_callback=update_progress
            )

        # Calculate statistics
        summary = calculate_summary_statistics(results, config)

        # Store results
        st.session_state.results = results
        st.session_state.summary = summary

        st.success(f"✓ Completed {len(results):,} simulations")
        progress_bar.empty()
        status_text.empty()


def render_results():
    st.header("Simulation Results")

    if st.session_state.summary is None:
        st.warning("⚠️ Please run simulation first")
        return

    summary = st.session_state.summary
    results = st.session_state.results

    # Summary statistics
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("MOIC Statistics")
        st.metric("Mean", f"{summary.mean_moic:.2f}x")
        st.metric("Median", f"{summary.median_moic:.2f}x")
        st.metric("Std Dev", f"{summary.std_moic:.2f}x")
        st.metric("5th Percentile", f"{summary.percentile_5_moic:.2f}x")
        st.metric("95th Percentile", f"{summary.percentile_95_moic:.2f}x")

    with col2:
        st.subheader("IRR Statistics")
        st.metric("Mean", f"{summary.mean_irr:.2%}")
        st.metric("Median", f"{summary.median_irr:.2%}")
        st.metric("Std Dev", f"{summary.std_irr:.2%}")
        st.metric("5th Percentile", f"{summary.percentile_5_irr:.2%}")
        st.metric("95th Percentile", f"{summary.percentile_95_irr:.2%}")

    # Histograms
    st.subheader("Distribution Plots")

    col1, col2 = st.columns(2)

    with col1:
        # MOIC histogram
        moics = [r.moic for r in results]
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=moics, nbinsx=50, name="MOIC"))
        fig.add_vline(x=summary.mean_moic, line_dash="dash", line_color="red",
                     annotation_text="Mean")
        fig.add_vline(x=summary.median_moic, line_dash="dash", line_color="green",
                     annotation_text="Median")
        fig.update_layout(title="MOIC Distribution", xaxis_title="MOIC", yaxis_title="Frequency")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # IRR histogram
        irrs = [r.irr * 100 for r in results]  # Convert to percentage
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=irrs, nbinsx=50, name="IRR"))
        fig.add_vline(x=summary.mean_irr * 100, line_dash="dash", line_color="red",
                     annotation_text="Mean")
        fig.add_vline(x=summary.median_irr * 100, line_dash="dash", line_color="green",
                     annotation_text="Median")
        fig.update_layout(title="IRR Distribution", xaxis_title="IRR (%)", yaxis_title="Frequency")
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
```

### Step 7.2: Run the Application

```bash
streamlit run app.py
```

---

## Phase 8: Testing & Validation

### Step 8.1: Create Comprehensive Test Suite

Create `tests/test_full_simulation.py`:

```python
from fund_simulation.data_import import parse_csv_file
from fund_simulation.models import SimulationConfiguration
from fund_simulation.simulation import run_monte_carlo_simulation
from fund_simulation.statistics import calculate_summary_statistics


def test_full_simulation():
    """Test complete simulation workflow."""

    # 1. Load data
    investments, errors = parse_csv_file('tests/sample_data.csv')
    assert len(investments) > 0
    assert len(errors) == 0

    # 2. Create configuration
    config = SimulationConfiguration(
        fund_name="Test Fund",
        fund_manager="Test Manager",
        simulation_count=1000  # Small for testing
    )
    errors = config.validate()
    assert len(errors) == 0

    # 3. Run simulation
    results = run_monte_carlo_simulation(investments, config)
    assert len(results) == 1000

    # 4. Calculate statistics
    summary = calculate_summary_statistics(results, config)
    assert summary.total_runs == 1000
    assert summary.mean_moic > 0
    assert summary.mean_irr != 0

    print("✓ Full simulation test passed")
    print(f"  Mean MOIC: {summary.mean_moic:.2f}x")
    print(f"  Mean IRR: {summary.mean_irr:.2%}")


if __name__ == "__main__":
    test_full_simulation()
    print("\n✓ All integration tests passed!")
```

---

## Phase 9: Deployment

### Step 9.1: Create README.md

```markdown
# Monte Carlo Fund Simulation

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## CSV Format

The application expects a CSV file with NO headers:

```
investment_name, fund_name, entry_date, latest_date, MOIC, IRR
```

Example:
```
Alibaba Group,Fund I,2011-04-20,2015-03-23,12.38,0.8983
Bazaarvoice,Fund I,2011-07-20,2012-09-10,0.88,-0.0381
```

## License

MIT
```

### Step 9.2: Create .gitignore

```.gitignore
venv/
__pycache__/
*.pyc
.DS_Store
temp_upload.csv
.streamlit/
```

---

## Success Criteria Checklist

- [ ] All data models implemented with validation
- [ ] Core calculators (holding period, IRR, MOIC) working correctly
- [ ] CSV import with comprehensive error handling
- [ ] Monte Carlo simulation engine functional
- [ ] Financial engineering (leverage, fees, carry) implemented
- [ ] Statistical analysis producing percentiles
- [ ] Streamlit UI with 4 pages operational
- [ ] Reproducible results (seed=42)
- [ ] Hash generation for deduplication
- [ ] Progress reporting during simulation
- [ ] Histogram visualization working
- [ ] All tests passing
- [ ] Documentation complete

---

**End of Implementation Blueprint**
