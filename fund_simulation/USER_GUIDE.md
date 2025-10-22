# Monte Carlo Fund Simulation - User Guide

## Quick Start

### Installation

1. **Run the installer**: Double-click `FundSimulation_Setup_v1.0.0.exe`
2. **Follow the wizard**: Click "Next" through the installation steps
3. **Choose installation location**: Default is `C:\Program Files\Monte Carlo Fund Simulation`
4. **Create shortcuts**: Check "Create desktop icon" if desired
5. **Complete installation**: Click "Finish"

### First Launch

1. **Double-click** the desktop icon or find "Monte Carlo Fund Simulation" in your Start Menu
2. **First-time setup**: The application will automatically:
   - Create a virtual environment (takes 1-2 minutes)
   - Install required packages
   - Start the application
3. **Browser opens**: The app will open in your default web browser at `http://localhost:8501`

**Note**: First launch takes 2-3 minutes. Subsequent launches are much faster (5-10 seconds).

---

## Using the Application

### 1. Data Import Tab

#### Import Investment Data

**Required CSV Format** (5 columns, NO headers):
```
Investment Name, Fund Name, Entry Date, MOIC, IRR
```

**Example:**
```
Company A, Fund I, 2020-01-15, 2.5, 0.25
Company B, Fund I, 2020-03-20, 1.8, 0.15
Company C, Fund II, 2021-06-10, 3.2, 0.35
```

**Column Details:**
- **Column 1**: Investment Name (e.g., "Company A")
- **Column 2**: Fund Name (e.g., "Fund I")
- **Column 3**: Entry Date (formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY)
- **Column 4**: MOIC (e.g., 2.5 for 2.5x return)
- **Column 5**: IRR (as decimal, e.g., 0.25 for 25%)

**Steps:**
1. Click "Browse files"
2. Select your CSV file
3. Review the data table
4. Check for any errors (shown in red)

#### Import Beta Price Data

**Required CSV Format** (2 columns):
```
Date, Price
2020-12-31, 100.00
2021-03-31, 105.00
2021-06-30, 103.00
```

**Supported Frequencies:**
- Daily
- Weekly
- Monthly (recommended)
- Quarterly
- Annual

**Steps:**
1. Click "Browse files" under "Beta Prices CSV"
2. Select your beta index file (e.g., S&P 500, Russell 2000)
3. Confirm the auto-detected frequency
4. Verify coverage (app checks if beta data covers all investment periods)

---

### 2. Configuration Tab

#### Fund Information
- **Fund Name**: Name of your fund
- **Fund Manager**: Manager name

#### Financial Parameters
- **Leverage Rate**: Leverage as % of LP capital (0-100%)
- **Cost of Capital**: Annual cost of debt (0-100%)
- **Management Fee Rate**: Annual management fee (0-10%)
- **Carry Rate**: Performance fee above hurdle (0-50%)
- **Hurdle Rate**: Minimum return before carry (0-100%)

#### Simulation Parameters
- **Number of Simulations**: How many portfolios to simulate (100-1,000,000)
  - Recommended: 10,000 for balance of speed vs accuracy
- **Portfolio Size (Mean)**: Average number of investments per portfolio
- **Portfolio Size (Std Dev)**: Variation in portfolio size

#### Beta Forward Simulation Settings
- **Simulation Horizon**: Number of **trading days** to project (252 = 1 year)
  - Default: 2,520 trading days = 10 years
- **Number of Beta Paths**: Monte Carlo paths for market simulation (100-10,000)
  - Default: 1,000

**Market Views:**
- **Return Outlook**:
  - Pessimistic = Historical - 10%
  - Base = Historical average
  - Optimistic = Historical + 10%
- **Volatility Confidence**:
  - Low = 1.5× historical volatility (more uncertainty)
  - Medium = 1.0× historical volatility
  - High = 0.5× historical volatility (more confident)

---

### 3. Run Simulation Tab

1. **Review summary**: Check simulation count and investment count
2. **Optional**: Check "Export detailed investment and cash flow data" for CSV export
3. **Click "▶️ Run Simulation"**
4. **Wait for completion**: Progress bar shows 4 stages:
   - Stage 0: Beta Decomposition
   - Stage 1: Alpha Simulation
   - Stage 2: Beta Forward Simulation
   - Stage 3: Gross Reconstruction
   - Stage 4: Net Reconstruction

**Typical Runtime:**
- 1,000 simulations: ~5 seconds
- 10,000 simulations: ~30 seconds
- 100,000 simulations: ~5 minutes

---

### 4. Results Tab

#### Export Results to Excel

**Click "📥 Export Results to Excel"** at the top of the Results tab.

**Excel Report Contents:**
- **Executive Summary**: Fund info, parameters, key metrics
- **Alpha Returns (Stage 1)**: Statistics and distribution charts
- **Beta Simulation (Stage 2)**: Market projections and terminal values
- **Gross Performance (Stage 3)**: Total returns with beta attribution
- **Net Performance (Stage 4)**: Final returns after all costs

**File saved as**: `{FundName}_Results_{timestamp}.xlsx`

#### Histogram Settings

**Click "📊 Histogram Settings"** to customize charts:
- **Number of Bins**: 10-200 (default: 50)
  - More bins = more detail, less bins = smoother
- **Histogram Type**:
  - Frequency: Raw counts
  - Probability Density: Normalized distribution

**Note**: Settings apply to both on-screen charts AND Excel export.

#### Understanding Results

**Stage 1: Alpha (Excess Returns)**
- Returns above the market benchmark
- Shows manager skill independent of market performance

**Stage 2: Beta Forward Simulation**
- Future market projections
- Median path shows expected market trajectory
- 5th/95th percentiles show range of outcomes

**Stage 3: Gross Performance**
- Total returns = Alpha × Beta
- Before management fees and carry

**Stage 4: Net Performance**
- Final LP returns after:
  - Management fees (2% default)
  - Carried interest (20% default above 8% hurdle)
  - Leverage costs

---

## Troubleshooting

### Application won't start

**Check:**
1. Is Python installed? Open Command Prompt and type: `python --version`
   - Should show Python 3.8 or higher
   - If not, download from: https://www.python.org/downloads/
2. Is there an error message in the black window?
   - Take a screenshot and contact support

### Browser doesn't open automatically

1. Wait 10 seconds for app to start
2. Manually open browser and go to: `http://localhost:8501`

### "Beta price data is required" error

**Solution:** You must upload beta prices in the Data Import tab before running simulation.

### CSV import errors

**Common issues:**
- Extra headers in CSV → Remove first row
- Wrong number of columns → Check you have exactly 5 columns for investments, 2 for beta
- Invalid dates → Use format YYYY-MM-DD
- IRR as percentage (25%) → Use decimal (0.25)

### Simulation takes too long

**Solutions:**
- Reduce number of simulations (try 1,000 for testing)
- Reduce number of beta paths (try 500)
- Close other programs to free up memory

### Excel export fails

**Check:**
1. Do you have Excel installed? (not required, but helps)
2. Is there a "Missing dependencies" error?
   - Open Command Prompt
   - Type: `cd "C:\Program Files\Monte Carlo Fund Simulation"`
   - Type: `venv\Scripts\pip install openpyxl kaleido`

---

## Tips & Best Practices

### Data Preparation

✅ **DO:**
- Use monthly beta data (easier to obtain than daily)
- Ensure beta data covers full investment period
- Use consistent date formats
- Remove any totals/summary rows from CSVs

❌ **DON'T:**
- Mix different benchmarks in beta data
- Include header rows in CSVs
- Use IRR as percentages (use decimals: 0.25 not 25%)

### Simulation Setup

**For initial testing:**
- 1,000-5,000 simulations
- 500-1,000 beta paths
- Base outlook, Medium confidence

**For final analysis:**
- 10,000-50,000 simulations
- 1,000-2,000 beta paths
- Adjust outlook/confidence based on market view

### Interpreting Results

**Focus on medians, not means:**
- Medians are more robust to outliers
- More representative of "typical" outcome

**Use percentiles for risk assessment:**
- 5th percentile = downside scenario
- Median = expected scenario
- 95th percentile = upside scenario

**Compare stages:**
- Alpha shows manager value-add
- Gross shows total value creation
- Net shows investor returns

---

## Getting Help

### Contact Support
- Email: support@yourcompany.com
- Documentation: [Link to internal docs]

### Common Questions

**Q: Can I save my configuration?**
A: Not currently. You'll need to re-enter parameters each session.

**Q: Can I export raw simulation data?**
A: Yes! Check "Export detailed data" in Run Simulation tab, then use the CSV export buttons in Results.

**Q: How do I stop the application?**
A: Close the black command window, or press Ctrl+C in it.

**Q: Can I run multiple simulations?**
A: Yes! Run a simulation, export results, then change parameters and run again.

**Q: Is my data saved?**
A: No, the app doesn't store data. Always export your results to Excel.

---

## Version History

### Version 1.0.0
- Initial release
- Monte Carlo simulation engine
- Alpha/beta decomposition
- Excel export with charts
- Interactive histogram controls
