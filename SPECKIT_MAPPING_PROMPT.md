# GitHub Speckit Project Mapping Prompt

**Project**: Monte Carlo Fund Simulation - Python Reimplementation

**Purpose**: This document instructs an agentic coding agent to use GitHub Speckit to thoroughly map and document the Monte Carlo Fund Simulation project before reimplementing it as a simple Python application.

---

## Overview

This project implements a Monte Carlo simulation engine for modeling future fund performance based on historical investment data. The system allows fund managers to:

1. Import historical investment data from CSV files
2. Configure simulation parameters (leverage, fees, carry, etc.)
3. Run thousands of Monte Carlo simulations
4. Visualize results with histograms and summary statistics
5. Save and compare multiple simulation runs

The original project was designed as a Windows desktop application (.NET 8 WPF), but a working Python implementation exists using Streamlit for the UI. Your task is to map out the EXACT mechanics of how the Monte Carlo simulation operates to enable a clean Python reimplementation.

---

## Critical: Monte Carlo Simulation Mechanics

The following describes the EXACT step-by-step process of how the Monte Carlo simulation engine operates. These details are critical for accurate reimplementation:

### 1. Data Ingestion Process

**CSV Format** (6 columns, NO headers):
```
investment_name, fund_name, entry_date, latest_date, MOIC, IRR
```

**Validation Rules**:
- **Column count**: Exactly 6 columns required
- **Dates**:
  - Multiple formats supported: `YYYY-MM-DD`, `MM/DD/YYYY`, `DD/MM/YYYY`, `YYYY/MM/DD`
  - Entry date MUST be before latest date
- **MOIC (Multiple on Invested Capital)**:
  - Must be positive (> 0)
  - Represents return multiple (e.g., 2.5 = 2.5x return)
- **IRR (Internal Rate of Return)**:
  - Decimal format (0.25 = 25%)
  - Cannot be less than -100% (-1.0)
  - Special case: IRR of exactly -1.0 is adjusted to -0.9999 to avoid division by zero
- **Logical consistency**: Entry date < Latest date

**Error Handling**:
- Row-specific error reporting with row number, column number, and field name
- Validation occurs BEFORE any simulation can run
- Duplicate detection: Investment name + Fund name combination should be unique

### 2. Configuration Parameters

**10 Required Configuration Fields**:

1. **Fund Name** (string): Name of the simulated fund
2. **Fund Manager** (string): Name of the fund manager
3. **Leverage Rate** (0-100%): Leverage applied to fund capital
4. **Cost of Capital** (0-100%): Annual cost of leverage/debt
5. **Management Fee Rate** (0-10%): Annual management fee on committed capital
6. **Carry Rate** (0-50%): Carried interest percentage on profits
7. **Hurdle Rate** (0-100%): Minimum return before carry is paid
8. **Simulation Count** (100-1,000,000): Number of Monte Carlo iterations to run
9. **Investment Count Mean** (≥1): Mean of normal distribution for portfolio size
10. **Investment Count Std Dev** (≥0): Standard deviation for portfolio size

**Hash Generation** (for deduplication):
- **Data Hash**: SHA256 hash of all investment records (sorted by investment name, fund name)
- **Total Hash**: SHA256 hash of Data Hash + all configuration parameters
- Used to prevent duplicate simulation runs

### 3. Single Simulation Iteration Logic

Each simulation iteration follows these EXACT steps:

#### Step 3.1: Generate Portfolio Size
```python
# Use normal distribution to determine number of investments
num_investments = round(normal_distribution(mean=config.investment_count_mean,
                                           std_dev=config.investment_count_std))
# Bound the value
num_investments = max(1, min(num_investments, len(investments) * 2))
```

#### Step 3.2: Random Investment Selection
```python
# Select investments WITH REPLACEMENT (same investment can be selected multiple times)
selected_investments = random_choice(investments, size=num_investments, replace=True)
```

#### Step 3.3: Calculate Holding Period for Each Investment

**Critical Formula**:
```python
# From MOIC and IRR, calculate days held using:
# MOIC = (1 + IRR)^(days/365)
# Therefore: days = 365 * ln(MOIC) / ln(1 + IRR)

days_held = 365 * log(MOIC) / log(1 + IRR)
days_held = round(days_held)  # Round to nearest integer
days_held = max(1, days_held)  # At least 1 day
```

**Edge Cases**:
- If MOIC = 0: Default to 365 days
- If MOIC < 0: Raise error
- If IRR = -1.0: Adjust to -0.9999
- If IRR < -1.0: Raise error
- If calculation fails: Default to 365 days

#### Step 3.4: Build Aggregate Cash Flow Schedule

**Investment Amount**: $1,000,000 per investment position

```python
cash_flows = {}  # Dictionary: {day: amount}
total_invested = 0

for each selected investment:
    investment_amount = 1_000_000
    total_invested += investment_amount

    # Calculate holding period
    days_held = calculate_holding_period(investment.moic, investment.irr)

    # Add exit cash flow
    exit_day = days_held
    exit_amount = investment_amount * investment.moic

    # Aggregate cash flows on same day
    if exit_day in cash_flows:
        cash_flows[exit_day] += exit_amount
    else:
        cash_flows[exit_day] = exit_amount
```

**Note**: Initial investment (-$1M per position on day 0) is NOT added to cash_flows dictionary but tracked separately as `total_invested`.

#### Step 3.5: Apply Financial Engineering

```python
# Calculate leverage
leverage_amount = total_invested * config.leverage_rate
total_capital = total_invested + leverage_amount

# Calculate time-weighted costs
max_day = max(cash_flows.keys()) if cash_flows else 365
years_held = max_day / 365.0

# Cost of leverage (simplified: paid at end)
leverage_cost = leverage_amount * config.cost_of_capital * years_held

# Management fees (on committed capital)
total_fees = total_capital * config.fee_rate * years_held

# Gross returns
total_returned = sum(cash_flows.values())
gross_profit = total_returned - total_capital

# Carry calculation (only on profits above hurdle)
hurdle_return = total_capital * (1 + config.hurdle_rate * years_held)
excess_return = max(0, total_returned - hurdle_return)
carry_paid = excess_return * config.carry_rate

# Net calculations (to Limited Partners)
net_returned = total_returned - leverage_cost - total_fees - carry_paid
net_profit = net_returned - total_invested
net_moic = net_returned / total_invested if total_invested > 0 else 0
```

#### Step 3.6: Calculate Net IRR

```python
# Proportionally reduce cash flows for fees and costs
reduction_factor = net_returned / total_returned if total_returned > 0 else 0

net_cash_flows = {}
for day, amount in cash_flows.items():
    net_cash_flows[day] = amount * reduction_factor

# Calculate IRR using Newton-Raphson method
net_irr = calculate_irr(net_cash_flows, total_invested)
```

**IRR Calculation (Newton-Raphson Method)**:
```python
def calculate_irr(cash_flows: dict, initial_investment: float) -> float:
    """
    Calculate IRR using Newton-Raphson method

    Args:
        cash_flows: {day: amount} dictionary
        initial_investment: Initial investment (positive number)

    Returns:
        IRR as decimal (e.g., 0.25 for 25%)
    """
    rate = 0.1  # Initial guess
    max_iterations = 100
    tolerance = 1e-6

    for iteration in range(max_iterations):
        # Calculate NPV and derivative
        npv = -initial_investment
        dnpv = 0

        for day, cash_flow in cash_flows.items():
            years = day / 365.0
            discount = (1 + rate) ** years
            npv += cash_flow / discount
            dnpv -= years * cash_flow / (discount * (1 + rate))

        # Check convergence
        if abs(npv) < tolerance:
            return rate

        # Newton-Raphson update
        if dnpv == 0:
            break

        rate = rate - npv / dnpv

        # Bound the rate
        rate = max(-0.9999, min(rate, 10.0))

    return rate
```

#### Step 3.7: Return Simulation Result

```python
SimulationResult(
    simulation_id=i,
    investments_selected=[list of investment names],
    investment_count=num_investments,
    total_invested=total_invested,
    total_returned=net_returned,
    moic=net_moic,
    irr=net_irr,
    gross_profit=gross_profit,
    net_profit=net_profit,
    fees_paid=total_fees,
    carry_paid=carry_paid,
    leverage_cost=leverage_cost
)
```

### 4. Full Monte Carlo Simulation Process

```python
def run_monte_carlo_simulation(investments, config):
    """
    Run complete Monte Carlo simulation

    Returns:
        (results_list, summary_statistics)
    """
    # Set random seed for reproducibility
    random_state = RandomState(seed=42)

    results = []
    for i in range(config.simulation_count):
        # Run single simulation
        result = run_single_simulation(investments, config, i, random_state)
        results.append(result)

        # Update progress every 100 simulations
        if (i + 1) % 100 == 0:
            report_progress(i + 1, config.simulation_count)

    # Calculate summary statistics
    moics = [r.moic for r in results]
    irrs = [r.irr for r in results]

    summary = SimulationSummary(
        total_runs=len(results),
        mean_moic=mean(moics),
        median_moic=median(moics),
        std_moic=std_dev(moics),
        percentile_5_moic=percentile(moics, 5),
        percentile_25_moic=percentile(moics, 25),
        percentile_75_moic=percentile(moics, 75),
        percentile_95_moic=percentile(moics, 95),
        mean_irr=mean(irrs),
        median_irr=median(irrs),
        std_irr=std_dev(irrs),
        percentile_5_irr=percentile(irrs, 5),
        percentile_25_irr=percentile(irrs, 25),
        percentile_75_irr=percentile(irrs, 75),
        percentile_95_irr=percentile(irrs, 95),
        timestamp=now()
    )

    return results, summary
```

### 5. Visualization & Results

**Histogram Generation**:
- 50 bins for both IRR and MOIC distributions
- X-axis: IRR (formatted as percentage) or MOIC (formatted as multiple)
- Y-axis: Frequency count
- Vertical lines for mean and median
- Clear labels and legends

**Summary Statistics Displayed**:
- Total simulation runs
- Mean, Median, Standard Deviation
- 5th, 25th, 75th, 95th percentiles
- Min and Max values

**Percentile Table**:
```
Percentile | MOIC      | IRR
-----------|-----------|---------
5th        | X.XXx     | XX.X%
25th       | X.XXx     | XX.X%
50th       | X.XXx     | XX.X%
75th       | X.XXx     | XX.X%
95th       | X.XXx     | XX.X%
```

---

## Data Models

### Investment
```python
@dataclass
class Investment:
    investment_name: str
    fund_name: str
    entry_date: datetime
    latest_date: datetime
    moic: float  # Multiple on Invested Capital
    irr: float   # Internal Rate of Return (decimal)

    @property
    def days_held(self) -> int:
        return (self.latest_date - self.entry_date).days

    def validate(self) -> List[str]:
        """Returns list of validation errors"""
        errors = []
        if not self.investment_name:
            errors.append("Investment name is required")
        if not self.fund_name:
            errors.append("Fund name is required")
        if self.entry_date >= self.latest_date:
            errors.append("Entry date must be before latest date")
        if self.moic < 0:
            errors.append("MOIC cannot be negative")
        if self.irr < -1.0:
            errors.append("IRR cannot be less than -100%")
        return errors
```

### SimulationConfiguration
```python
@dataclass
class SimulationConfiguration:
    leverage_rate: float = 0.0
    cost_of_capital: float = 0.08
    fee_rate: float = 0.02
    carry_rate: float = 0.20
    hurdle_rate: float = 0.08
    simulation_count: int = 10000
    investment_count_mean: float = 10.0
    investment_count_std: float = 2.0
    fund_name: str = ""
    fund_manager: str = ""
    data_hash: str = ""
    total_hash: str = ""

    def validate(self) -> List[str]:
        """Returns list of validation errors"""
        errors = []
        if not (0 <= self.leverage_rate <= 1):
            errors.append("Leverage rate must be 0-100%")
        if not (0 <= self.cost_of_capital <= 1):
            errors.append("Cost of capital must be 0-100%")
        if not (0 <= self.fee_rate <= 0.1):
            errors.append("Fee rate must be 0-10%")
        if not (0 <= self.carry_rate <= 0.5):
            errors.append("Carry rate must be 0-50%")
        if not (0 <= self.hurdle_rate <= 1):
            errors.append("Hurdle rate must be 0-100%")
        if not (100 <= self.simulation_count <= 1000000):
            errors.append("Simulation count must be 100-1,000,000")
        if self.investment_count_mean < 1:
            errors.append("Investment count mean must be ≥ 1")
        if self.investment_count_std < 0:
            errors.append("Investment count std dev cannot be negative")
        if not self.fund_name:
            errors.append("Fund name is required")
        if not self.fund_manager:
            errors.append("Fund manager is required")
        return errors

    def generate_hash(self, investments: List[Investment]) -> Tuple[str, str]:
        """Generate data hash and total hash"""
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
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()

        # Total hash: SHA256 of data hash + configuration
        config_data = {
            'data_hash': data_hash,
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
        total_hash = hashlib.sha256(total_str.encode()).hexdigest()

        self.data_hash = data_hash
        self.total_hash = total_hash

        return data_hash, total_hash
```

### SimulationResult
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

### SimulationSummary
```python
@dataclass
class SimulationSummary:
    config: SimulationConfiguration
    total_runs: int
    mean_moic: float
    median_moic: float
    std_moic: float
    percentile_5_moic: float
    percentile_25_moic: float
    percentile_75_moic: float
    percentile_95_moic: float
    mean_irr: float
    median_irr: float
    std_irr: float
    percentile_5_irr: float
    percentile_25_irr: float
    percentile_75_irr: float
    percentile_95_irr: float
    timestamp: datetime
```

---

## Project File Locations

### Current Python Implementation
- **Main application**: `python/app.py` - Streamlit UI with 4 pages (Data Import, Configuration, Run Simulation, Results)
- **Simulation engine**: `python/simulation.py` - Core Monte Carlo logic
- **Data models**: `python/models.py` - All data classes
- **Data import**: `python/data_import.py` - CSV parsing and validation
- **Requirements**: `python/requirements.txt` - Dependencies (streamlit, pandas, numpy, plotly)

### Documentation
- **Main README**: `README.md` - Overview and technology stack (.NET WPF)
- **Python README**: `python/README.md` - Python version documentation
- **Specification**: `.specify/specs/001-monte-carlo-fund-simulation/spec.md` - Detailed requirements
- **Architecture**: `.specify/specs/001-monte-carlo-fund-simulation/architecture-overview.md` - System design
- **Data Model**: `.specify/specs/001-monte-carlo-fund-simulation/data-model.md` - Entity definitions
- **Implementation Plan**: `.specify/specs/001-monte-carlo-fund-simulation/plan.md` - Phased roadmap

---

## Instructions for Agentic Coding Agent

### Task: Use GitHub Speckit to Map the Project

You are to use GitHub Speckit's analysis capabilities to thoroughly map this Monte Carlo Fund Simulation project. Follow these steps:

#### 1. Project Discovery Phase
- [ ] Use Speckit to identify all project files and their purposes
- [ ] Map the directory structure and document file relationships
- [ ] Identify entry points (app.py for Python, planned WPF for .NET)
- [ ] Document all dependencies and external libraries

#### 2. Code Flow Analysis
- [ ] Trace the complete data flow from CSV import to results display
- [ ] Map the simulation execution flow step-by-step
- [ ] Identify all calculation functions and their mathematical formulas
- [ ] Document error handling and validation logic

#### 3. Data Model Mapping
- [ ] Document all data classes/models and their properties
- [ ] Map relationships between data entities
- [ ] Identify validation rules for each model
- [ ] Document hash generation logic for deduplication

#### 4. Calculation Engine Analysis
- [ ] Document the exact holding period calculation formula
- [ ] Map the IRR calculation algorithm (Newton-Raphson)
- [ ] Document MOIC calculation logic
- [ ] Identify all edge cases and their handling

#### 5. Financial Engineering Mechanics
- [ ] Document leverage application logic
- [ ] Map fee calculation (management fees)
- [ ] Document carry calculation (carried interest)
- [ ] Map hurdle rate application
- [ ] Document cost of capital calculations

#### 6. Statistical Analysis Mapping
- [ ] Document summary statistics calculations
- [ ] Map percentile calculations
- [ ] Identify histogram generation logic
- [ ] Document data visualization requirements

#### 7. Configuration & Validation
- [ ] Map all 10 configuration parameters
- [ ] Document validation rules for each parameter
- [ ] Identify hash generation for data and total hash
- [ ] Map duplicate detection logic

#### 8. User Interface Flow
- [ ] Document the 4-page workflow (Data Import → Configuration → Run Simulation → Results)
- [ ] Map user inputs and outputs for each page
- [ ] Identify progress reporting mechanisms
- [ ] Document error message display logic

#### 9. Performance Considerations
- [ ] Identify performance targets (1,000 sims in 5 sec, 10,000 in 60 sec)
- [ ] Document random number generation (seed = 42 for reproducibility)
- [ ] Map progress callback mechanism
- [ ] Identify opportunities for optimization

#### 10. Create Comprehensive Documentation
Generate the following Speckit artifacts:

**a) Architecture Map**
- Complete system architecture diagram
- Data flow diagrams
- Component interaction diagrams

**b) Technical Specification**
- Detailed specification of all algorithms
- Mathematical formulas with explanations
- Edge case documentation
- Validation rules catalog

**c) API/Interface Documentation**
- All function signatures
- Input/output specifications
- Error conditions and handling
- Example usage

**d) Implementation Guide**
- Step-by-step reimplementation instructions
- Critical calculation formulas
- Required libraries and dependencies
- Testing requirements

**e) Test Cases**
- Unit test scenarios for each calculator
- Integration test scenarios
- Edge case test data
- Expected outputs for validation

#### 11. Validation Checklist

Ensure the mapping captures:
- [ ] Exact formula for holding period calculation: `days = 365 * ln(MOIC) / ln(1 + IRR)`
- [ ] Newton-Raphson IRR calculation with max 100 iterations, tolerance 1e-6
- [ ] Random selection WITH REPLACEMENT
- [ ] Normal distribution for portfolio size with rounding
- [ ] $1M per investment position assumption
- [ ] Aggregate cash flow dictionary structure
- [ ] Leverage, fees, carry, and hurdle calculations in exact order
- [ ] Reduction factor for net cash flows
- [ ] Hash generation using SHA256 with sorted data
- [ ] 50 bins for histograms
- [ ] Percentiles: 5th, 25th, 50th (median), 75th, 95th
- [ ] Random seed = 42 for reproducibility
- [ ] Progress reporting every 100 simulations

---

## Expected Deliverables

After completing the Speckit mapping, you should produce:

1. **Project Map** - Complete file structure with purpose of each file
2. **Algorithm Specifications** - Detailed documentation of all calculations
3. **Data Flow Diagrams** - Visual representation of data processing
4. **Implementation Blueprint** - Step-by-step guide for Python reimplementation
5. **Test Specifications** - Comprehensive test cases with expected results
6. **Configuration Guide** - Documentation of all parameters and validation rules
7. **Performance Benchmarks** - Expected performance targets and optimization notes

---

## Success Criteria

The mapping is complete when:
- ✅ Every calculation formula is documented with examples
- ✅ All data models are specified with validation rules
- ✅ The complete simulation flow is diagrammed step-by-step
- ✅ Edge cases are identified and documented
- ✅ Performance targets are clearly stated
- ✅ Test cases cover all critical paths
- ✅ A developer could reimplement the system from the documentation alone
- ✅ All financial engineering mechanics are explained in detail
- ✅ Hash generation and deduplication logic is clear
- ✅ The exact random number generation strategy is documented

---

## Key Formulas Reference

**Holding Period Calculation**:
```
days = 365 * ln(MOIC) / ln(1 + IRR)
```

**MOIC Calculation**:
```
MOIC = Total Inflows / Total Outflows
```

**Net MOIC**:
```
Net MOIC = Net Returned / Total Invested
```

**IRR Calculation** (Newton-Raphson):
```
NPV = -Initial_Investment + Σ(CF_i / (1 + r)^(days_i/365))
dNPV/dr = -Σ(years_i * CF_i / ((1 + r)^(years_i+1)))
r_new = r_old - NPV / (dNPV/dr)
```

**Leverage**:
```
Leverage Amount = Total Invested × Leverage Rate
Total Capital = Total Invested + Leverage Amount
```

**Fees**:
```
Total Fees = Total Capital × Fee Rate × Years Held
```

**Carry**:
```
Hurdle Return = Total Capital × (1 + Hurdle Rate × Years Held)
Excess Return = max(0, Total Returned - Hurdle Return)
Carry Paid = Excess Return × Carry Rate
```

**Net Returns**:
```
Net Returned = Total Returned - Leverage Cost - Fees - Carry
Net Profit = Net Returned - Total Invested (excludes leverage)
```

---

## Notes for Implementation

1. **Reproducibility**: Random seed = 42 ensures identical results for same inputs
2. **Sampling**: Investments selected WITH REPLACEMENT (same investment can appear multiple times)
3. **Portfolio Size**: Normally distributed, rounded to integer, bounded [1, 2×input_count]
4. **Cash Flows**: Aggregated by day (multiple exits on same day are summed)
5. **Time Basis**: All calculations use 365-day year
6. **Precision**: Round to 6 decimal places for hash generation
7. **Progress**: Report every 100 simulations to avoid UI lag
8. **Edge Cases**: Handle IRR = -1.0, MOIC = 0, division by zero, convergence failures

---

## Final Instruction

Create a complete, detailed project map using GitHub Speckit that captures every aspect of this Monte Carlo simulation engine. The documentation should be so thorough that a developer with no prior knowledge of the system could reimplement it exactly, producing identical results for the same input data and configuration.

Focus especially on:
- **Mathematical precision** - Exact formulas, not approximations
- **Algorithm details** - Step-by-step logic, not high-level descriptions
- **Edge case handling** - What happens when calculations fail
- **Data structures** - Exact format of dictionaries, lists, objects
- **Validation logic** - Complete rules with examples
- **Financial mechanics** - Precise order of operations for fees, carry, leverage

This mapping will serve as the specification for a clean Python reimplementation of the Monte Carlo fund simulation engine.
