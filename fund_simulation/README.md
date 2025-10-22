# Monte Carlo Fund Simulation

A Python implementation of a Monte Carlo simulation engine for modeling future fund performance based on historical investment data.

## Features

- **CSV Data Import** - Load historical investment data with comprehensive validation
- **Monte Carlo Simulation** - Run thousands of simulations with configurable parameters
- **Financial Engineering** - Model leverage, management fees, carried interest, and hurdle rates
- **Statistical Analysis** - Calculate mean, median, percentiles, and distributions
- **Interactive UI** - Streamlit-based web interface with 4-page workflow
- **Reproducible Results** - Fixed random seed (42) ensures identical results for same inputs

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Run the Streamlit App

```bash
streamlit run app.py
```

Then open your browser to the URL shown (typically http://localhost:8501)

### Run Test Simulation

```bash
python test_simulation.py
```

## CSV Format

The application expects a CSV file with **NO headers** and exactly **6 columns**:

```
investment_name, fund_name, entry_date, latest_date, MOIC, IRR
```

**Example:**
```csv
Alibaba Group,Fund I,2011-04-20,2015-03-23,12.38,0.8983
Bazaarvoice,Fund I,2011-07-20,2012-09-10,0.88,-0.0381
DrillingInfo,Fund I,2012-02-29,2018-08-01,3.44,0.2138
```

**Field Details:**
- **investment_name**: Name of portfolio company
- **fund_name**: Name of fund that made investment
- **entry_date**: Date investment was made (YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, or YYYY/MM/DD)
- **latest_date**: Date of exit or most recent valuation
- **MOIC**: Multiple on Invested Capital (e.g., 2.5 = 2.5x return)
- **IRR**: Internal Rate of Return as decimal (e.g., 0.25 = 25%)

## Configuration Parameters

### Fund Information
- **Fund Name**: Name of simulated fund
- **Fund Manager**: Name of fund manager

### Financial Parameters
- **Leverage Rate** (0-100%): Leverage as % of LP capital
- **Cost of Capital** (0-100%): Annual cost of debt/leverage
- **Management Fee Rate** (0-10%): Annual management fee on committed capital
- **Carry Rate** (0-50%): Carried interest percentage on profits
- **Hurdle Rate** (0-100%): Minimum return before carry is paid

### Simulation Parameters
- **Simulation Count** (100-1,000,000): Number of Monte Carlo iterations
- **Portfolio Size Mean** (≥1): Average number of investments per simulation
- **Portfolio Size Std Dev** (≥0): Standard deviation for portfolio size

## Usage Workflow

### 1. Data Import
- Upload CSV file with historical investment data
- System validates all fields and displays any errors
- View loaded investments in table format

### 2. Configuration
- Set fund information (name, manager)
- Configure financial parameters (leverage, fees, carry, hurdle)
- Set simulation parameters (count, portfolio size)
- System validates all parameters

### 3. Run Simulation
- Click "Run Simulation" button
- Progress bar shows completion percentage
- Simulation uses fixed random seed (42) for reproducibility

### 4. View Results
- **Summary Statistics**: Mean, median, std dev, min, max
- **Percentile Table**: 5th, 25th, 50th, 75th, 95th percentiles
- **Distribution Plots**: Histograms for MOIC and IRR with mean/median lines

## How It Works

### Monte Carlo Process

Each simulation iteration:

1. **Generate Portfolio Size** - Sample from normal distribution (mean, std dev)
2. **Select Investments** - Randomly select WITH REPLACEMENT (allows concentration)
3. **Build Cash Flows** - Calculate holding period and exit proceeds for each investment
4. **Apply Financial Engineering**:
   - Calculate total capital (LP + leverage)
   - Calculate gross returns
   - Deduct leverage costs
   - Deduct management fees
   - Calculate carry on excess returns above hurdle
   - Calculate net returns to LPs
5. **Calculate Net IRR** - Using Newton-Raphson method
6. **Return Results** - MOIC, IRR, and financial details

### Key Formulas

**Holding Period:**
```
days = 365 × ln(MOIC) / ln(1 + IRR)
```

**IRR (Newton-Raphson):**
```
NPV(r) = -Initial_Investment + Σ(CF_i / (1 + r)^(days_i/365))
r_new = r_old - NPV(r_old) / (dNPV/dr)(r_old)
```

**Financial Engineering:**
```
Leverage Amount = LP Capital × Leverage Rate
Total Capital = LP Capital + Leverage Amount
Management Fees = Total Capital × Fee Rate × Years Held
Hurdle Return = Total Capital × (1 + Hurdle Rate × Years Held)
Carry = max(0, Total Returned - Hurdle Return) × Carry Rate
Net Returned = Total Returned - Leverage Cost - Fees - Carry
Net MOIC = Net Returned / LP Capital
```

## Test Results

**Test Run:** 1,000 simulations with 107 real investments (Lead Edge Capital data)

**Results:**
- Mean MOIC: 1.98x
- Median MOIC: 1.93x
- Mean IRR: 25.02%
- Median IRR: 24.49%
- 5th Percentile MOIC: 1.42x
- 95th Percentile MOIC: 2.68x

## Project Structure

```
fund_simulation/
├── fund_simulation/
│   ├── __init__.py
│   ├── models.py           # Data models
│   ├── calculators.py      # Core calculations
│   ├── data_import.py      # CSV parsing
│   ├── simulation.py       # Monte Carlo engine
│   └── statistics.py       # Statistical analysis
├── app.py                  # Streamlit UI
├── test_simulation.py      # Test script
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Documentation

Complete documentation is available in the following files:

- **TECHNICAL_SPECIFICATION.md** - Complete algorithmic specification
- **ARCHITECTURE_AND_DATA_FLOW.md** - System architecture and data flows
- **IMPLEMENTATION_BLUEPRINT.md** - Step-by-step implementation guide
- **TEST_SPECIFICATIONS.md** - Comprehensive test cases
- **API_DOCUMENTATION.md** - Complete API reference
- **PROJECT_MAPPING_SUMMARY.md** - Executive overview

## Performance

- **1,000 simulations**: < 5 seconds
- **10,000 simulations**: < 60 seconds (target)
- **100,000 simulations**: < 15 minutes (target)

## Reproducibility

The simulation uses a fixed random seed (42) to ensure reproducible results:
- Same input data + same configuration → identical results
- Enables testing, debugging, and result verification
- Change seed in `simulation.py` to explore different scenarios

## Edge Cases

The system handles:
- IRR = -100% (adjusted to -99.99%)
- MOIC = 0 (total loss)
- Zero investments (validation error)
- Invalid dates, negative MOIC, IRR < -100%
- Missing fields, wrong column count
- Duplicate investments (warning)

## Dependencies

- Python 3.8+
- streamlit >= 1.28.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- plotly >= 5.17.0
- python-dateutil >= 2.8.2

## License

MIT License

## Author

Implementation based on specifications from Monte Carlo Fund Simulation project mapping.

---

**Status:** Production-ready implementation with comprehensive testing and validation.
