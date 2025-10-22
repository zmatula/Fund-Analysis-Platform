# Monte Carlo Fund Simulation - Technical Specification

**Version:** 1.0
**Last Updated:** 2025-10-19
**Status:** Complete Specification for Python Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Data Models](#data-models)
4. [Core Algorithms](#core-algorithms)
5. [Financial Engineering Mechanics](#financial-engineering-mechanics)
6. [Validation Rules](#validation-rules)
7. [Performance Requirements](#performance-requirements)
8. [Edge Cases & Error Handling](#edge-cases--error-handling)

---

## Executive Summary

The Monte Carlo Fund Simulation Engine is a statistical modeling system that simulates future fund performance based on historical investment data. The system uses Monte Carlo methods to generate thousands of possible portfolio outcomes, providing probabilistic forecasts of fund returns through MOIC (Multiple on Invested Capital) and IRR (Internal Rate of Return) distributions.

### Key Features
- CSV-based historical data import with comprehensive validation
- Configurable simulation parameters (leverage, fees, carry, hurdle rate)
- Monte Carlo simulation engine with reproducible random seed
- Statistical analysis with percentile distributions
- Histogram visualization of results
- Hash-based deduplication to prevent duplicate runs

---

## System Overview

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  Page 1: Data Import    │ Page 2: Configuration             │
│  Page 3: Run Simulation │ Page 4: Results & Visualization   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  • CSV Parser & Validator                                    │
│  • Configuration Manager                                     │
│  • Hash Generator (SHA256)                                   │
│  • Simulation Engine                                         │
│  • Statistics Calculator                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     CALCULATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  • Holding Period Calculator                                 │
│  • IRR Calculator (Newton-Raphson)                           │
│  • MOIC Calculator                                           │
│  • Cash Flow Aggregator                                      │
│  • Financial Engineering Processor                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATA LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  • Investment Records                                        │
│  • Simulation Results                                        │
│  • Summary Statistics                                        │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
CSV File → Validation → Investment Objects → Configuration →
Monte Carlo Engine → Individual Simulations → Aggregate Results →
Statistical Analysis → Visualization
```

---

## Data Models

### 1. Investment

The core data entity representing a single historical investment.

```python
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
            errors.append(f"Entry date ({self.entry_date}) must be before latest date ({self.latest_date})")

        if self.moic < 0:
            errors.append(f"MOIC ({self.moic}) cannot be negative")

        if self.irr < -1.0:
            errors.append(f"IRR ({self.irr:.2%}) cannot be less than -100%")

        return errors
```

### 2. SimulationConfiguration

Configuration parameters for a Monte Carlo simulation run.

```python
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
    leverage_rate: float = 0.0          # 0-100% (stored as 0.0-1.0)
    cost_of_capital: float = 0.08       # 0-100% (stored as 0.0-1.0)
    fee_rate: float = 0.02              # 0-10% (stored as 0.0-0.1)
    carry_rate: float = 0.20            # 0-50% (stored as 0.0-0.5)
    hurdle_rate: float = 0.08           # 0-100% (stored as 0.0-1.0)

    # Simulation Parameters
    simulation_count: int = 10000       # 100-1,000,000
    investment_count_mean: float = 10.0 # ≥1
    investment_count_std: float = 2.0   # ≥0

    # Deduplication Hashes
    data_hash: str = ""
    total_hash: str = ""

    def validate(self) -> List[str]:
        """
        Validate configuration parameters.

        Returns:
            List of error messages (empty if valid)
        """
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
        """
        Generate SHA256 hashes for deduplication.

        Args:
            investments: List of investment objects

        Returns:
            Tuple of (data_hash, total_hash)
        """
        import hashlib
        import json

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

### 3. SimulationResult

Result of a single Monte Carlo simulation iteration.

```python
@dataclass
class SimulationResult:
    """
    Result from a single Monte Carlo simulation iteration.

    This captures the complete financial outcome for one simulated portfolio.
    """
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

### 4. SimulationSummary

Aggregate statistics from all simulation iterations.

```python
@dataclass
class SimulationSummary:
    """
    Statistical summary of Monte Carlo simulation results.

    Contains percentile distributions for both MOIC and IRR.
    """
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

## Core Algorithms

### Algorithm 1: Holding Period Calculation

**Purpose:** Calculate the number of days an investment was held based on MOIC and IRR.

**Mathematical Foundation:**

The relationship between MOIC, IRR, and time is:

```
MOIC = (1 + IRR)^(days/365)
```

Solving for days:

```
days = 365 × ln(MOIC) / ln(1 + IRR)
```

**Python Implementation:**

```python
def calculate_holding_period(moic: float, irr: float) -> int:
    """
    Calculate holding period in days from MOIC and IRR.

    Formula: days = 365 × ln(MOIC) / ln(1 + IRR)

    Args:
        moic: Multiple on Invested Capital (must be > 0)
        irr: Internal Rate of Return as decimal (must be > -1.0)

    Returns:
        Number of days (minimum 1)

    Edge Cases:
        - MOIC ≤ 0: Returns 365 (default)
        - IRR = -1.0: Adjusted to -0.9999 to avoid log(0)
        - Calculation failure: Returns 365 (default)
    """
    import math

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

**Example Calculations:**

| MOIC | IRR    | Formula                          | Days |
|------|--------|----------------------------------|------|
| 2.0  | 0.25   | 365 × ln(2.0) / ln(1.25)         | 1134 |
| 1.5  | 0.15   | 365 × ln(1.5) / ln(1.15)         | 1049 |
| 3.0  | 0.50   | 365 × ln(3.0) / ln(1.50)         | 989  |
| 0.5  | -0.20  | 365 × ln(0.5) / ln(0.80)         | 1136 |

**Edge Case Examples:**

| MOIC  | IRR    | Handling                        | Result |
|-------|--------|---------------------------------|--------|
| 0     | 0.25   | MOIC ≤ 0 → default              | 365    |
| -0.5  | 0.25   | MOIC ≤ 0 → default              | 365    |
| 2.0   | -1.0   | IRR = -1.0 → adjust to -0.9999  | 253    |
| 2.0   | -1.01  | IRR < -1.0 → should be rejected | Error  |

---

### Algorithm 2: IRR Calculation (Newton-Raphson Method)

**Purpose:** Calculate Internal Rate of Return from cash flows using iterative numerical method.

**Mathematical Foundation:**

IRR is the discount rate `r` where Net Present Value (NPV) = 0:

```
NPV = -Initial_Investment + Σ(CF_i / (1 + r)^(t_i / 365))
```

Newton-Raphson iteratively improves the estimate:

```
r_new = r_old - NPV(r_old) / (dNPV/dr)(r_old)
```

Derivative of NPV:

```
dNPV/dr = -Σ(t_i/365 × CF_i / (1 + r)^(t_i/365 + 1))
```

**Python Implementation:**

```python
def calculate_irr(cash_flows: Dict[int, float], initial_investment: float) -> float:
    """
    Calculate IRR using Newton-Raphson method.

    Args:
        cash_flows: Dictionary mapping day → cash flow amount
        initial_investment: Initial investment (positive number)

    Returns:
        IRR as decimal (e.g., 0.25 for 25%)

    Convergence:
        - Max iterations: 100
        - Tolerance: 1e-6
        - Initial guess: 0.1 (10%)
        - Rate bounds: [-0.9999, 10.0]
    """
    rate = 0.1  # Initial guess
    max_iterations = 100
    tolerance = 1e-6

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

**Example Calculation:**

```
Initial Investment: $1,000,000
Cash Flows:
  Day 730 (2 years): $1,500,000

Iteration 1:
  r = 0.1
  NPV = -1,000,000 + 1,500,000 / (1.1)^2 = 239,669
  dNPV/dr = -2 × 1,500,000 / (1.1)^3 = -2,253,944
  r_new = 0.1 - 239,669 / (-2,253,944) = 0.2064

Iteration 2:
  r = 0.2064
  NPV = -1,000,000 + 1,500,000 / (1.2064)^2 = 31,250
  ...continues until convergence...

Final IRR ≈ 0.2247 (22.47%)
```

---

### Algorithm 3: Portfolio Size Generation

**Purpose:** Determine number of investments for each simulation using normal distribution.

**Implementation:**

```python
def generate_portfolio_size(mean: float, std_dev: float,
                           max_investments: int,
                           random_state: np.random.RandomState) -> int:
    """
    Generate portfolio size from normal distribution.

    Args:
        mean: Mean number of investments
        std_dev: Standard deviation
        max_investments: Maximum possible value
        random_state: NumPy random state for reproducibility

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
```

**Example:**

```
Mean = 10, Std Dev = 2, Max Investments = 50

Sample 1: normal(10, 2) → 11.3 → round → 11
Sample 2: normal(10, 2) → 8.7 → round → 9
Sample 3: normal(10, 2) → 13.9 → round → 14
Sample 4: normal(10, 2) → -1.2 → round → -1 → bounded to 1
Sample 5: normal(10, 2) → 105.3 → round → 105 → bounded to 100
```

---

### Algorithm 4: Random Investment Selection

**Purpose:** Select investments for a simulation with replacement.

**Implementation:**

```python
def select_investments(investments: List[Investment],
                      count: int,
                      random_state: np.random.RandomState) -> List[Investment]:
    """
    Randomly select investments WITH REPLACEMENT.

    This means the same investment can appear multiple times in a portfolio,
    simulating concentration risk.

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

**Example:**

```
Universe: [A, B, C, D, E]
Count: 10

Selected: [A, C, C, B, E, A, D, C, A, B]
          ↑     ↑                 ↑
          └─────┴─────────────────┘
          Investment 'A' selected 3 times
          Investment 'C' selected 3 times
```

---

## Financial Engineering Mechanics

### Overview

The financial engineering layer applies realistic fund economics:
1. **Leverage** - Borrowing to amplify returns
2. **Management Fees** - Annual fees on committed capital
3. **Carried Interest (Carry)** - Performance fee on profits above hurdle
4. **Cost of Capital** - Interest on borrowed funds

### Calculation Sequence

**CRITICAL:** Operations must occur in this exact order:

```
1. Calculate Total Capital (invested + leverage)
2. Calculate Gross Returns (from investment performance)
3. Calculate Time-Weighted Costs
4. Apply Hurdle Rate
5. Calculate Carry on Excess Returns
6. Calculate Net Returns to LPs
```

### Step-by-Step Process

#### Step 1: Calculate Total Capital

```python
# LP Capital (Limited Partners)
total_invested = investment_count × 1_000_000

# Leverage (borrowed funds)
leverage_amount = total_invested × config.leverage_rate

# Total Capital Deployed
total_capital = total_invested + leverage_amount
```

**Example:**
```
Investments: 10
Total Invested: $10,000,000
Leverage Rate: 50% (0.5)
Leverage Amount: $5,000,000
Total Capital: $15,000,000
```

#### Step 2: Calculate Holding Period

```python
# Find maximum exit day from all cash flows
max_day = max(cash_flows.keys()) if cash_flows else 365

# Convert to years
years_held = max_day / 365.0
```

#### Step 3: Calculate Gross Returns

```python
# Sum all exit proceeds
total_returned = sum(cash_flows.values())

# Gross profit before any fees
gross_profit = total_returned - total_capital
```

**Example:**
```
Total Returned: $20,000,000
Total Capital: $15,000,000
Gross Profit: $5,000,000
Gross MOIC: 20M / 15M = 1.33x
```

#### Step 4: Calculate Time-Weighted Costs

```python
# Cost of Leverage (interest on debt)
leverage_cost = leverage_amount × config.cost_of_capital × years_held

# Management Fees (on total capital)
management_fees = total_capital × config.fee_rate × years_held
```

**Example:**
```
Years Held: 3.5
Leverage Amount: $5,000,000
Cost of Capital: 8% per year
Leverage Cost: $5M × 0.08 × 3.5 = $1,400,000

Total Capital: $15,000,000
Fee Rate: 2% per year
Management Fees: $15M × 0.02 × 3.5 = $1,050,000
```

#### Step 5: Calculate Hurdle and Carry

```python
# Calculate hurdle return threshold
hurdle_return = total_capital × (1 + config.hurdle_rate × years_held)

# Calculate excess return above hurdle
excess_return = max(0, total_returned - hurdle_return)

# Carry is percentage of excess return
carry_paid = excess_return × config.carry_rate
```

**Example:**
```
Total Capital: $15,000,000
Hurdle Rate: 8% per year
Years Held: 3.5
Hurdle Return: $15M × (1 + 0.08 × 3.5) = $19,200,000

Total Returned: $20,000,000
Excess Return: max(0, $20M - $19.2M) = $800,000

Carry Rate: 20%
Carry Paid: $800,000 × 0.20 = $160,000
```

**Note:** If total_returned < hurdle_return, excess = 0 and carry = 0.

#### Step 6: Calculate Net Returns to LPs

```python
# Net proceeds after all fees and costs
net_returned = total_returned - leverage_cost - management_fees - carry_paid

# Net profit to LPs (excludes leverage)
net_profit = net_returned - total_invested

# Net MOIC (on LP capital only, not total capital)
net_moic = net_returned / total_invested if total_invested > 0 else 0
```

**Example:**
```
Total Returned: $20,000,000
Leverage Cost: -$1,400,000
Management Fees: -$1,050,000
Carry Paid: -$160,000
──────────────────────────
Net Returned: $17,390,000

Total Invested (LP Capital): $10,000,000
Net Profit: $17,390,000 - $10,000,000 = $7,390,000
Net MOIC: $17,390,000 / $10,000,000 = 1.739x
```

### Complete Example

```
Configuration:
- LP Capital: $10,000,000
- Leverage Rate: 50%
- Cost of Capital: 8%
- Management Fee: 2%
- Carry Rate: 20%
- Hurdle Rate: 8%
- Years Held: 3.5

Step 1: Total Capital
- Leverage: $10M × 0.5 = $5M
- Total Capital: $10M + $5M = $15M

Step 2: Gross Returns
- Total Returned: $20M
- Gross Profit: $20M - $15M = $5M
- Gross MOIC: 1.33x

Step 3: Costs
- Leverage Cost: $5M × 0.08 × 3.5 = $1.4M
- Management Fees: $15M × 0.02 × 3.5 = $1.05M

Step 4: Carry
- Hurdle Return: $15M × (1 + 0.08 × 3.5) = $19.2M
- Excess: $20M - $19.2M = $0.8M
- Carry: $0.8M × 0.20 = $0.16M

Step 5: Net to LPs
- Net Returned: $20M - $1.4M - $1.05M - $0.16M = $17.39M
- Net Profit: $17.39M - $10M = $7.39M
- Net MOIC: 1.739x
```

---

## Validation Rules

### CSV Import Validation

#### Column Count
- **Rule:** Exactly 6 columns required
- **Error:** "Expected 6 columns, found {count} in row {row_num}"

#### Column 1: Investment Name
- **Rule:** Non-empty string
- **Error:** "Investment name is required in row {row_num}"

#### Column 2: Fund Name
- **Rule:** Non-empty string
- **Error:** "Fund name is required in row {row_num}"

#### Column 3: Entry Date
- **Rule:** Valid date in supported formats
- **Formats:** YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, YYYY/MM/DD
- **Error:** "Invalid entry date '{value}' in row {row_num}"

#### Column 4: Latest Date
- **Rule:** Valid date, must be after entry date
- **Error:** "Invalid latest date '{value}' in row {row_num}"
- **Error:** "Latest date must be after entry date in row {row_num}"

#### Column 5: MOIC
- **Rule:** Numeric, must be positive (> 0)
- **Error:** "Invalid MOIC '{value}' in row {row_num}"
- **Error:** "MOIC must be positive in row {row_num}"

#### Column 6: IRR
- **Rule:** Numeric, must be ≥ -1.0 (≥ -100%)
- **Error:** "Invalid IRR '{value}' in row {row_num}"
- **Error:** "IRR cannot be less than -100% in row {row_num}"
- **Special:** IRR = -1.0 adjusted to -0.9999

#### Duplicate Detection
- **Rule:** (Investment Name, Fund Name) combination should be unique
- **Warning:** "Duplicate investment '{name}' in fund '{fund}' (rows {row_nums})"

### Configuration Validation

| Parameter                | Rule              | Error Message                                |
|--------------------------|-------------------|----------------------------------------------|
| Fund Name                | Required string   | "Fund name is required"                      |
| Fund Manager             | Required string   | "Fund manager is required"                   |
| Leverage Rate            | 0% - 100%         | "Leverage rate must be 0-100%"               |
| Cost of Capital          | 0% - 100%         | "Cost of capital must be 0-100%"             |
| Management Fee Rate      | 0% - 10%          | "Fee rate must be 0-10%"                     |
| Carry Rate               | 0% - 50%          | "Carry rate must be 0-50%"                   |
| Hurdle Rate              | 0% - 100%         | "Hurdle rate must be 0-100%"                 |
| Simulation Count         | 100 - 1,000,000   | "Simulation count must be 100-1,000,000"     |
| Investment Count Mean    | ≥ 1               | "Investment count mean must be ≥ 1"          |
| Investment Count Std Dev | ≥ 0               | "Investment count std dev cannot be negative"|

---

## Performance Requirements

### Target Performance

| Simulations | Target Time | Acceptable Time |
|-------------|-------------|-----------------|
| 1,000       | < 5 sec     | < 10 sec        |
| 10,000      | < 60 sec    | < 120 sec       |
| 100,000     | < 10 min    | < 15 min        |

### Optimization Strategies

1. **Reproducibility**
   - Use fixed random seed (42) for identical results
   - Allows debugging and result verification

2. **Progress Reporting**
   - Report progress every 100 simulations
   - Prevents UI lag while providing feedback

3. **Vectorization**
   - Use NumPy for numerical operations
   - Batch calculations where possible

4. **Memory Efficiency**
   - Aggregate cash flows by day (reduce dictionary size)
   - Store only necessary result fields

---

## Edge Cases & Error Handling

### Edge Case 1: IRR = -100%

**Scenario:** Investment is a total loss

**Input:**
```
MOIC = 0
IRR = -1.0
```

**Handling:**
```python
if irr == -1.0:
    irr = -0.9999  # Avoid log(0) in calculations
```

**Impact:**
- Holding period calculation uses adjusted IRR
- Prevents mathematical errors

### Edge Case 2: Zero MOIC

**Scenario:** Investment returned nothing

**Input:**
```
MOIC = 0
```

**Handling:**
```python
if moic <= 0:
    days_held = 365  # Default to 1 year
```

### Edge Case 3: Portfolio Size Bounds

**Scenario:** Normal distribution generates unrealistic values

**Examples:**
```
Generated: -5 → Bounded to: 1
Generated: 250 (max=50) → Bounded to: 100
```

**Handling:**
```python
size = max(1, min(size, max_investments * 2))
```

### Edge Case 4: IRR Convergence Failure

**Scenario:** Newton-Raphson doesn't converge in 100 iterations

**Handling:**
```python
# Return best estimate after max iterations
return rate
```

**Note:** Rare in practice with reasonable cash flows

### Edge Case 5: No Excess Return

**Scenario:** Returns don't exceed hurdle

**Input:**
```
Total Returned: $15,000,000
Hurdle Return: $19,200,000
```

**Handling:**
```python
excess_return = max(0, total_returned - hurdle_return)
# excess_return = 0
# carry_paid = 0
```

### Edge Case 6: Zero Total Returned

**Scenario:** All investments failed

**Handling:**
```python
reduction_factor = net_returned / total_returned if total_returned > 0 else 0
# reduction_factor = 0
# All net cash flows = 0
# Net IRR calculation may fail → return -0.9999
```

---

## Random Number Generation

### Reproducibility

**Critical:** Use fixed random seed for reproducible results.

```python
import numpy as np

# Initialize at start of simulation
random_state = np.random.RandomState(seed=42)

# Use throughout simulation
portfolio_size = random_state.normal(mean, std_dev)
selected_indices = random_state.choice(n, size=k, replace=True)
```

**Why seed=42:**
- Industry standard "answer to everything"
- Allows regression testing
- Enables result verification
- Supports debugging

**Testing Different Scenarios:**
- Change seed to explore sensitivity
- Document seed changes in results
- Compare distributions across seeds

---

## Hash Generation for Deduplication

### Purpose

Prevent duplicate simulation runs with identical inputs.

### Data Hash

**Captures:** Investment data only

```python
# Sort investments by (name, fund) for consistency
sorted_investments = sorted(investments, key=lambda x: (x.name, x.fund))

# Round floats to 6 decimal places
investment_data = [
    {
        'name': inv.investment_name,
        'fund': inv.fund_name,
        'entry': inv.entry_date.isoformat(),
        'latest': inv.latest_date.isoformat(),
        'moic': round(inv.moic, 6),
        'irr': round(inv.irr, 6)
    }
    for inv in sorted_investments
]

# JSON serialize with sorted keys
json_str = json.dumps(investment_data, sort_keys=True)

# SHA256 hash
data_hash = hashlib.sha256(json_str.encode()).hexdigest()
```

### Total Hash

**Captures:** Data hash + configuration

```python
config_data = {
    'data_hash': data_hash,  # Include data hash
    'leverage_rate': round(config.leverage_rate, 6),
    'cost_of_capital': round(config.cost_of_capital, 6),
    'fee_rate': round(config.fee_rate, 6),
    'carry_rate': round(config.carry_rate, 6),
    'hurdle_rate': round(config.hurdle_rate, 6),
    'simulation_count': config.simulation_count,
    'investment_count_mean': round(config.investment_count_mean, 6),
    'investment_count_std': round(config.investment_count_std, 6),
    'fund_name': config.fund_name,
    'fund_manager': config.fund_manager
}

json_str = json.dumps(config_data, sort_keys=True)
total_hash = hashlib.sha256(json_str.encode()).hexdigest()
```

### Usage

```python
# Before running simulation
data_hash, total_hash = config.generate_hash(investments)

# Check if already run
if total_hash in previous_runs:
    raise ValueError("This simulation has already been run")

# Store hash with results
results.total_hash = total_hash
```

---

## Summary

This technical specification provides complete documentation of the Monte Carlo Fund Simulation engine, including:

✅ **Data Models** - All classes with validation logic
✅ **Core Algorithms** - Step-by-step mathematical formulas
✅ **Financial Engineering** - Exact calculation sequence
✅ **Validation Rules** - Comprehensive error checking
✅ **Edge Cases** - Complete exception handling
✅ **Performance Targets** - Benchmarks and optimization
✅ **Reproducibility** - Random seed management
✅ **Deduplication** - Hash generation strategy

A developer can implement the complete system from this specification alone, producing identical results for identical inputs.

---

**End of Technical Specification**
