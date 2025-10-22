# Monte Carlo Fund Simulation - API Documentation

**Version:** 1.0
**Last Updated:** 2025-10-19

---

## Table of Contents

1. [Module Overview](#module-overview)
2. [Data Models API](#data-models-api)
3. [Calculators API](#calculators-api)
4. [Data Import API](#data-import-api)
5. [Simulation API](#simulation-api)
6. [Statistics API](#statistics-api)
7. [Usage Examples](#usage-examples)

---

## Module Overview

### Package Structure

```
fund_simulation/
├── __init__.py
├── models.py           # Data classes
├── calculators.py      # Core calculations
├── data_import.py      # CSV parsing
├── simulation.py       # Monte Carlo engine
├── statistics.py       # Statistical analysis
├── visualization.py    # Charting (optional)
└── utils.py           # Helper functions
```

### Import Conventions

```python
# Import data models
from fund_simulation.models import (
    Investment,
    SimulationConfiguration,
    SimulationResult,
    SimulationSummary
)

# Import calculators
from fund_simulation.calculators import (
    calculate_holding_period,
    calculate_irr,
    calculate_moic
)

# Import data import
from fund_simulation.data_import import parse_csv_file

# Import simulation engine
from fund_simulation.simulation import (
    run_monte_carlo_simulation,
    run_single_simulation,
    generate_portfolio_size,
    select_investments
)

# Import statistics
from fund_simulation.statistics import calculate_summary_statistics
```

---

## Data Models API

### Investment

**Purpose:** Represents a single historical investment with performance data.

```python
@dataclass
class Investment:
    investment_name: str
    fund_name: str
    entry_date: datetime
    latest_date: datetime
    moic: float
    irr: float
```

#### Constructor

```python
Investment(
    investment_name: str,
    fund_name: str,
    entry_date: datetime,
    latest_date: datetime,
    moic: float,
    irr: float
)
```

**Parameters:**
- `investment_name` (str): Name of the portfolio company
- `fund_name` (str): Name of the fund that made the investment
- `entry_date` (datetime): Date when investment was made
- `latest_date` (datetime): Date of most recent valuation or exit
- `moic` (float): Multiple on Invested Capital (e.g., 2.5 = 2.5x return)
- `irr` (float): Internal Rate of Return as decimal (e.g., 0.25 = 25%)

**Example:**

```python
from datetime import datetime

investment = Investment(
    investment_name="Alibaba Group",
    fund_name="Fund I",
    entry_date=datetime(2011, 4, 20),
    latest_date=datetime(2015, 3, 23),
    moic=12.38,
    irr=0.8983
)
```

#### Properties

##### `days_held`

```python
@property
def days_held(self) -> int
```

**Returns:** Number of calendar days between entry and latest date.

**Example:**

```python
days = investment.days_held
print(f"Investment held for {days} days")  # Output: Investment held for 1433 days
```

#### Methods

##### `validate()`

```python
def validate(self) -> List[str]
```

**Returns:** List of validation error messages (empty if valid).

**Validation Rules:**
- Investment name must be non-empty
- Fund name must be non-empty
- Entry date must be before latest date
- MOIC must be non-negative
- IRR must be ≥ -1.0 (-100%)

**Example:**

```python
errors = investment.validate()
if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    print("Investment is valid")
```

---

### SimulationConfiguration

**Purpose:** Configuration parameters for Monte Carlo simulation.

```python
@dataclass
class SimulationConfiguration:
    fund_name: str = ""
    fund_manager: str = ""
    leverage_rate: float = 0.0
    cost_of_capital: float = 0.08
    fee_rate: float = 0.02
    carry_rate: float = 0.20
    hurdle_rate: float = 0.08
    simulation_count: int = 10000
    investment_count_mean: float = 10.0
    investment_count_std: float = 2.0
    data_hash: str = ""
    total_hash: str = ""
```

#### Constructor

```python
SimulationConfiguration(
    fund_name: str = "",
    fund_manager: str = "",
    leverage_rate: float = 0.0,
    cost_of_capital: float = 0.08,
    fee_rate: float = 0.02,
    carry_rate: float = 0.20,
    hurdle_rate: float = 0.08,
    simulation_count: int = 10000,
    investment_count_mean: float = 10.0,
    investment_count_std: float = 2.0
)
```

**Parameters:**
- `fund_name` (str): Name of the simulated fund
- `fund_manager` (str): Name of the fund manager
- `leverage_rate` (float): Leverage as decimal (0.5 = 50%)
- `cost_of_capital` (float): Annual cost of debt as decimal (0.08 = 8%)
- `fee_rate` (float): Annual management fee as decimal (0.02 = 2%)
- `carry_rate` (float): Carried interest rate as decimal (0.20 = 20%)
- `hurdle_rate` (float): Hurdle rate as decimal (0.08 = 8%)
- `simulation_count` (int): Number of Monte Carlo iterations (100-1,000,000)
- `investment_count_mean` (float): Mean portfolio size
- `investment_count_std` (float): Standard deviation of portfolio size

**Example:**

```python
config = SimulationConfiguration(
    fund_name="Venture Fund III",
    fund_manager="Jane Doe",
    leverage_rate=0.5,        # 50% leverage
    cost_of_capital=0.08,     # 8% cost of debt
    fee_rate=0.02,            # 2% annual fee
    carry_rate=0.20,          # 20% carry
    hurdle_rate=0.08,         # 8% hurdle
    simulation_count=10000,
    investment_count_mean=12.0,
    investment_count_std=3.0
)
```

#### Methods

##### `validate()`

```python
def validate(self) -> List[str]
```

**Returns:** List of validation error messages (empty if valid).

**Validation Rules:**
- Fund name and manager required
- Leverage rate: 0-100%
- Cost of capital: 0-100%
- Fee rate: 0-10%
- Carry rate: 0-50%
- Hurdle rate: 0-100%
- Simulation count: 100-1,000,000
- Investment count mean: ≥1
- Investment count std: ≥0

**Example:**

```python
errors = config.validate()
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
```

##### `generate_hash()`

```python
def generate_hash(investments: List[Investment]) -> Tuple[str, str]
```

**Parameters:**
- `investments` (List[Investment]): Investment universe

**Returns:** Tuple of (data_hash, total_hash) as hex strings.

**Purpose:** Generate SHA256 hashes for deduplication.

**Example:**

```python
data_hash, total_hash = config.generate_hash(investments)
print(f"Data Hash: {data_hash[:16]}...")
print(f"Total Hash: {total_hash[:16]}...")
```

---

### SimulationResult

**Purpose:** Result from a single Monte Carlo simulation iteration.

```python
@dataclass
class SimulationResult:
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
```

**Fields:**
- `simulation_id` (int): Unique ID for this simulation iteration
- `investments_selected` (List[str]): Names of selected investments
- `investment_count` (int): Number of investments in portfolio
- `total_invested` (float): Total LP capital invested
- `total_returned` (float): Net cash returned to LPs
- `moic` (float): Net Multiple on Invested Capital
- `irr` (float): Net Internal Rate of Return
- `gross_profit` (float): Profit before fees and costs
- `net_profit` (float): Profit after all fees and costs
- `fees_paid` (float): Total management fees
- `carry_paid` (float): Carried interest paid
- `leverage_cost` (float): Cost of leverage

---

### SimulationSummary

**Purpose:** Aggregate statistics from all simulation iterations.

```python
@dataclass
class SimulationSummary:
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

---

## Calculators API

### calculate_holding_period()

**Purpose:** Calculate holding period in days from MOIC and IRR.

```python
def calculate_holding_period(moic: float, irr: float) -> int
```

**Parameters:**
- `moic` (float): Multiple on Invested Capital (must be > 0)
- `irr` (float): Internal Rate of Return as decimal (must be > -1.0)

**Returns:** Number of days (minimum 1)

**Formula:** `days = 365 × ln(MOIC) / ln(1 + IRR)`

**Edge Cases:**
- MOIC ≤ 0: Returns 365 (default)
- IRR = -1.0: Adjusted to -0.9999 to avoid log(0)
- Calculation failure: Returns 365 (default)

**Example:**

```python
from fund_simulation.calculators import calculate_holding_period

# Calculate holding period for 2x return at 25% IRR
days = calculate_holding_period(moic=2.0, irr=0.25)
print(f"Holding period: {days} days")  # Output: ~1134 days
```

---

### calculate_irr()

**Purpose:** Calculate Internal Rate of Return using Newton-Raphson method.

```python
def calculate_irr(
    cash_flows: Dict[int, float],
    initial_investment: float,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> float
```

**Parameters:**
- `cash_flows` (Dict[int, float]): Dictionary mapping day → cash flow amount
- `initial_investment` (float): Initial investment (positive number)
- `max_iterations` (int): Maximum iterations for convergence (default: 100)
- `tolerance` (float): Convergence tolerance (default: 1e-6)

**Returns:** IRR as decimal (e.g., 0.25 for 25%)

**Convergence:**
- Initial guess: 0.1 (10%)
- Rate bounds: [-0.9999, 10.0]
- Returns best estimate even if not converged

**Example:**

```python
from fund_simulation.calculators import calculate_irr

# $1M invested, $1.5M returned after 2 years
cash_flows = {730: 1_500_000}
irr = calculate_irr(cash_flows, 1_000_000)
print(f"IRR: {irr:.2%}")  # Output: IRR: 22.47%
```

**Multiple Cash Flows:**

```python
# $2M invested, $500K after 1 year, $2M after 3 years
cash_flows = {
    365: 500_000,
    1095: 2_000_000
}
irr = calculate_irr(cash_flows, 2_000_000)
print(f"IRR: {irr:.2%}")
```

---

### calculate_moic()

**Purpose:** Calculate Multiple on Invested Capital.

```python
def calculate_moic(total_returned: float, total_invested: float) -> float
```

**Parameters:**
- `total_returned` (float): Total cash returned
- `total_invested` (float): Total cash invested

**Returns:** MOIC (e.g., 2.5 for 2.5x return)

**Edge Case:** Returns 0.0 if total_invested ≤ 0 (avoids division by zero)

**Example:**

```python
from fund_simulation.calculators import calculate_moic

moic = calculate_moic(total_returned=2_500_000, total_invested=1_000_000)
print(f"MOIC: {moic:.2f}x")  # Output: MOIC: 2.50x
```

---

## Data Import API

### parse_csv_file()

**Purpose:** Parse CSV file and return Investment objects.

```python
def parse_csv_file(file_path: str) -> Tuple[List[Investment], List[str]]
```

**Parameters:**
- `file_path` (str): Path to CSV file

**Returns:** Tuple of (investments, errors)
- `investments` (List[Investment]): Successfully parsed investments
- `errors` (List[str]): Validation error messages

**CSV Format:**
- NO headers
- 6 columns: investment_name, fund_name, entry_date, latest_date, MOIC, IRR
- Supported date formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, YYYY/MM/DD

**Special Handling:**
- IRR = -1.0 is automatically adjusted to -0.9999
- UTF-8 with BOM support (encoding='utf-8-sig')
- Empty rows are skipped
- Duplicate (name, fund) combinations generate warnings

**Example:**

```python
from fund_simulation.data_import import parse_csv_file

investments, errors = parse_csv_file('investments.csv')

if errors:
    print("Errors found:")
    for error in errors:
        print(f"  - {error}")

print(f"Loaded {len(investments)} investments")

for inv in investments[:5]:
    print(f"{inv.investment_name}: {inv.moic:.2f}x, {inv.irr:.2%}")
```

**Error Examples:**

```
Row 5: Expected 6 columns, found 5
Row 12: Invalid entry date '2023-13-45'
Row 23: MOIC must be positive in row 23
Row 34: IRR cannot be less than -100% in row 34
```

---

## Simulation API

### run_monte_carlo_simulation()

**Purpose:** Run complete Monte Carlo simulation.

```python
def run_monte_carlo_simulation(
    investments: List[Investment],
    config: SimulationConfiguration,
    progress_callback: Optional[Callable[[float], None]] = None
) -> List[SimulationResult]
```

**Parameters:**
- `investments` (List[Investment]): Investment universe
- `config` (SimulationConfiguration): Simulation configuration
- `progress_callback` (Optional[Callable]): Progress callback function (receives float 0.0-1.0)

**Returns:** List of SimulationResult objects

**Random Seed:** Fixed at 42 for reproducibility

**Progress Updates:** Called every 100 simulations

**Example:**

```python
from fund_simulation.simulation import run_monte_carlo_simulation

def show_progress(fraction):
    print(f"Progress: {fraction*100:.1f}%")

results = run_monte_carlo_simulation(
    investments,
    config,
    progress_callback=show_progress
)

print(f"Completed {len(results)} simulations")
```

---

### run_single_simulation()

**Purpose:** Run a single Monte Carlo simulation iteration.

```python
def run_single_simulation(
    investments: List[Investment],
    config: SimulationConfiguration,
    simulation_id: int,
    random_state: np.random.RandomState
) -> SimulationResult
```

**Parameters:**
- `investments` (List[Investment]): Available investment universe
- `config` (SimulationConfiguration): Simulation configuration
- `simulation_id` (int): ID for this simulation
- `random_state` (np.random.RandomState): NumPy random state

**Returns:** SimulationResult object

**Process:**
1. Generate portfolio size (normal distribution)
2. Select investments WITH REPLACEMENT
3. Build cash flow schedule
4. Calculate total capital (with leverage)
5. Calculate gross returns
6. Apply financial engineering (fees, carry, leverage cost)
7. Calculate net returns
8. Calculate net IRR

**Example:**

```python
import numpy as np
from fund_simulation.simulation import run_single_simulation

random_state = np.random.RandomState(seed=42)

result = run_single_simulation(
    investments,
    config,
    simulation_id=0,
    random_state=random_state
)

print(f"Simulation 0:")
print(f"  Portfolio size: {result.investment_count}")
print(f"  Net MOIC: {result.moic:.2f}x")
print(f"  Net IRR: {result.irr:.2%}")
```

---

### generate_portfolio_size()

**Purpose:** Generate portfolio size from normal distribution.

```python
def generate_portfolio_size(
    mean: float,
    std_dev: float,
    max_investments: int,
    random_state: np.random.RandomState
) -> int
```

**Parameters:**
- `mean` (float): Mean number of investments
- `std_dev` (float): Standard deviation
- `max_investments` (int): Maximum possible value
- `random_state` (np.random.RandomState): NumPy random state

**Returns:** Integer portfolio size bounded [1, 2 × max_investments]

**Example:**

```python
import numpy as np
from fund_simulation.simulation import generate_portfolio_size

random_state = np.random.RandomState(seed=42)

size = generate_portfolio_size(
    mean=10.0,
    std_dev=2.0,
    max_investments=50,
    random_state=random_state
)

print(f"Portfolio size: {size}")  # Output: Portfolio size: 11
```

---

### select_investments()

**Purpose:** Randomly select investments WITH REPLACEMENT.

```python
def select_investments(
    investments: List[Investment],
    count: int,
    random_state: np.random.RandomState
) -> List[Investment]
```

**Parameters:**
- `investments` (List[Investment]): Available investment universe
- `count` (int): Number of investments to select
- `random_state` (np.random.RandomState): NumPy random state

**Returns:** List of selected investments (may contain duplicates)

**Note:** Uses `replace=True` to allow concentration (same investment multiple times)

**Example:**

```python
import numpy as np
from fund_simulation.simulation import select_investments

random_state = np.random.RandomState(seed=42)

selected = select_investments(investments, count=10, random_state=random_state)

# Count duplicates
from collections import Counter
counts = Counter(inv.investment_name for inv in selected)
print("Selected investments:")
for name, count in counts.most_common():
    print(f"  {name}: {count}x")
```

---

## Statistics API

### calculate_summary_statistics()

**Purpose:** Calculate summary statistics from simulation results.

```python
def calculate_summary_statistics(
    results: List[SimulationResult],
    config: SimulationConfiguration
) -> SimulationSummary
```

**Parameters:**
- `results` (List[SimulationResult]): List of simulation results
- `config` (SimulationConfiguration): Configuration used for simulation

**Returns:** SimulationSummary object with all statistics

**Statistics Calculated:**
- Mean, median, std dev, min, max
- Percentiles: 5th, 25th, 75th, 95th
- Calculated for both MOIC and IRR

**Example:**

```python
from fund_simulation.statistics import calculate_summary_statistics

summary = calculate_summary_statistics(results, config)

print("MOIC Statistics:")
print(f"  Mean: {summary.mean_moic:.2f}x")
print(f"  Median: {summary.median_moic:.2f}x")
print(f"  5th Percentile: {summary.percentile_5_moic:.2f}x")
print(f"  95th Percentile: {summary.percentile_95_moic:.2f}x")

print("\nIRR Statistics:")
print(f"  Mean: {summary.mean_irr:.2%}")
print(f"  Median: {summary.median_irr:.2%}")
print(f"  5th Percentile: {summary.percentile_5_irr:.2%}")
print(f"  95th Percentile: {summary.percentile_95_irr:.2%}")
```

---

## Usage Examples

### Example 1: Basic Workflow

```python
from fund_simulation.data_import import parse_csv_file
from fund_simulation.models import SimulationConfiguration
from fund_simulation.simulation import run_monte_carlo_simulation
from fund_simulation.statistics import calculate_summary_statistics

# 1. Load data
investments, errors = parse_csv_file('investments.csv')
if errors:
    print("Errors:", errors)
    exit(1)

print(f"Loaded {len(investments)} investments")

# 2. Configure simulation
config = SimulationConfiguration(
    fund_name="Demo Fund",
    fund_manager="Demo Manager",
    leverage_rate=0.0,
    simulation_count=10000,
    investment_count_mean=15.0,
    investment_count_std=3.0
)

# 3. Validate configuration
errors = config.validate()
if errors:
    print("Config errors:", errors)
    exit(1)

# 4. Run simulation
print("Running simulation...")
results = run_monte_carlo_simulation(investments, config)

# 5. Calculate statistics
summary = calculate_summary_statistics(results, config)

# 6. Display results
print(f"\nResults ({summary.total_runs} simulations):")
print(f"Mean MOIC: {summary.mean_moic:.2f}x")
print(f"Mean IRR: {summary.mean_irr:.2%}")
```

### Example 2: Custom Progress Tracking

```python
import time

class ProgressTracker:
    def __init__(self):
        self.start_time = time.time()

    def update(self, fraction):
        elapsed = time.time() - self.start_time
        remaining = elapsed / fraction - elapsed if fraction > 0 else 0
        print(f"\rProgress: {fraction*100:.1f}% | "
              f"Elapsed: {elapsed:.1f}s | "
              f"Remaining: {remaining:.1f}s", end='')

tracker = ProgressTracker()
results = run_monte_carlo_simulation(
    investments,
    config,
    progress_callback=tracker.update
)
print()  # New line after progress
```

### Example 3: Analyzing Individual Results

```python
# Find best and worst simulations
results_sorted = sorted(results, key=lambda r: r.moic)
worst = results_sorted[0]
best = results_sorted[-1]

print("Worst Case:")
print(f"  MOIC: {worst.moic:.2f}x")
print(f"  IRR: {worst.irr:.2%}")
print(f"  Portfolio size: {worst.investment_count}")

print("\nBest Case:")
print(f"  MOIC: {best.moic:.2f}x")
print(f"  IRR: {best.irr:.2%}")
print(f"  Portfolio size: {best.investment_count}")

# Analyze portfolio composition
from collections import Counter
all_investments = []
for result in results:
    all_investments.extend(result.investments_selected)

counts = Counter(all_investments)
print("\nMost frequently selected investments:")
for name, count in counts.most_common(10):
    frequency = count / len(results)
    print(f"  {name}: {count} times ({frequency:.1%})")
```

### Example 4: Comparing Scenarios

```python
# Compare different leverage scenarios
leverage_rates = [0.0, 0.25, 0.5, 0.75, 1.0]

for leverage_rate in leverage_rates:
    config.leverage_rate = leverage_rate

    results = run_monte_carlo_simulation(investments, config)
    summary = calculate_summary_statistics(results, config)

    print(f"\nLeverage: {leverage_rate:.0%}")
    print(f"  Mean MOIC: {summary.mean_moic:.2f}x")
    print(f"  Mean IRR: {summary.mean_irr:.2%}")
    print(f"  Std Dev MOIC: {summary.std_moic:.2f}x")
```

---

**End of API Documentation**
