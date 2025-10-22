# Monte Carlo Fund Simulation - First-Time User Guide

**Welcome!** This guide will walk you through using the Monte Carlo Fund Simulation application for the first time.

---

## Table of Contents

1. [What This Application Does](#what-this-application-does)
2. [Installation](#installation)
3. [First Launch](#first-launch)
4. [Getting Started - Your First Simulation](#getting-started---your-first-simulation)
5. [Understanding the Interface](#understanding-the-interface)
6. [Step-by-Step Walkthrough](#step-by-step-walkthrough)
7. [Understanding Your Results](#understanding-your-results)
8. [Exporting Results](#exporting-results)
9. [Common Questions](#common-questions)
10. [Troubleshooting](#troubleshooting)

---

## What This Application Does

The Monte Carlo Fund Simulation helps you:

✅ **Predict future fund performance** based on historical investment data
✅ **Understand risk and variability** in fund returns
✅ **Separate alpha (skill) from beta (market exposure)**
✅ **Model different market scenarios** (optimistic, base, pessimistic)
✅ **Generate professional reports** for stakeholders

**You don't need to know programming or statistics** - the application handles all the complex calculations for you.

---

## Installation

### Step 1: Run the Installer

1. Locate the file: `FundSimulation_WithPython_Setup_v1.0.0.exe`
2. Double-click to run it
3. If you see a "Windows Protected Your PC" warning:
   - Click **"More info"**
   - Click **"Run anyway"**
   - This is normal for new software

### Step 2: Follow the Setup Wizard

1. **Welcome Screen** → Click **"Next"**
2. **Choose Install Location** → Use default location → Click **"Next"**
3. **Select Components** → Leave everything checked → Click **"Next"**
4. **Additional Tasks** → ✅ Check "Create a desktop icon" → Click **"Next"**
5. **Ready to Install** → Click **"Install"**
6. **Wait** (~10 seconds)
7. **Completing Setup** → ✅ Check "Launch Monte Carlo Fund Simulation" → Click **"Finish"**

### Step 3: No Additional Software Needed!

✅ Python is included
✅ All required packages are included
✅ Everything installs automatically

**You're done with installation!**

---

## First Launch

### What to Expect on First Run

When you launch the application for the first time, you'll see a **black console window** with installation progress:

```
========================================
  Monte Carlo Fund Simulation
  Version 1.0.0
========================================

Initializing...

----------------------------------------
  FIRST-TIME SETUP
----------------------------------------

This is your first time running the application.
Installing required packages...

This will take 2-3 minutes. Please wait.
```

**Don't close this window!** It's installing necessary software packages.

### Installation Progress

You'll see three steps:

```
[1/3] Checking for pip package manager...
      ✓ Pip already available

[2/3] Upgrading pip to latest version...
      ✓ Pip upgraded

[3/3] Installing application packages:
      - streamlit (web framework)
      - pandas (data processing)
      - plotly (charts and graphs)
      - numpy (numerical computing)
      - openpyxl (Excel export)
      - kaleido (chart rendering)
      - and more...

      This may take 2-3 minutes...
```

**⏱️ Time:** 2-3 minutes (one time only)
**☕ Grab a coffee!**

### Setup Complete

When installation finishes, you'll see:

```
========================================
  ✓ SETUP COMPLETE!
========================================

All packages installed successfully.
Starting application...

========================================
  LAUNCHING APPLICATION
========================================

Opening browser at http://localhost:8501
```

**Your browser will open automatically** with the application running!

### Keep the Console Window Open

**IMPORTANT:** Don't close the black console window! The application needs it to run.

- ✅ **Minimize it** if you want
- ❌ **Don't close it** or the app will stop

---

## Getting Started - Your First Simulation

### What You'll Need

Before you begin, prepare:

1. **Historical Investment Data** (CSV file)
   - Investment names
   - Entry dates
   - MOIC (Multiple on Invested Capital)
   - IRR (Internal Rate of Return)

2. **Beta Price Data** (CSV file)
   - Historical market index prices (e.g., S&P 500, Russell 2000)
   - Dates and prices

---

## Understanding the Interface

### The Four Tabs

When the application opens in your browser, you'll see **4 tabs** at the top:

#### 📁 **Tab 1: Data Import**
- Upload your historical investment data
- Upload beta price index data
- Preview your data

#### ⚙️ **Tab 2: Configuration**
- Set fund parameters (fees, carry, leverage)
- Configure simulation settings
- Set market outlook

#### ▶️ **Tab 3: Run Simulation**
- Start the Monte Carlo simulation
- Monitor progress
- See completion status

#### 📈 **Tab 4: Results**
- View charts and statistics
- Analyze performance distributions
- Export results to Excel or CSV

---

## Step-by-Step Walkthrough

### Tab 1: Data Import

#### Step 1.1: Prepare Your Investment Data CSV

Your CSV file should have **5 columns, NO headers**:

```
Investment Name, Fund Name, Entry Date, MOIC, IRR
Deal_A, Fund_I, 2018-01-15, 2.5, 0.25
Deal_B, Fund_I, 2018-03-20, 1.8, 0.18
Deal_C, Fund_II, 2019-06-10, 3.2, 0.35
```

**Format Notes:**
- **Investment Name:** Any text (e.g., "Company A", "Deal_123")
- **Fund Name:** Any text (e.g., "Fund I", "Growth Fund")
- **Entry Date:** YYYY-MM-DD format (e.g., 2018-01-15)
- **MOIC:** Decimal (e.g., 2.5 means 2.5x return)
- **IRR:** Decimal (e.g., 0.25 means 25% IRR)
- **NO headers** in the first row!

#### Step 1.2: Upload Investment Data

1. Click **"Browse files"** under "Upload CSV file"
2. Select your investment CSV file
3. Click **"Open"**

**What happens:**
- Application reads your file
- Calculates exit dates automatically
- Shows a preview table
- Displays success message: "✓ Successfully loaded X investments"

**Check the preview table** to make sure your data loaded correctly!

#### Step 1.3: Prepare Beta Price Data (Optional)

Your beta CSV should have **2 columns** (headers optional):

```
Date, Price
2015-01-01, 2058.90
2015-02-01, 2104.50
2015-03-01, 2067.89
```

**Format Notes:**
- **Date:** Various formats accepted (YYYY-MM-DD, MM/DD/YYYY, etc.)
- **Price:** Any number (index price or level)

#### Step 1.4: Upload Beta Price Data

1. Scroll down to "Import Beta Price Data"
2. Click **"Browse files"** under "Upload Beta Prices CSV"
3. Select your beta CSV file
4. Click **"Open"**

**What happens:**
- Application auto-detects frequency (daily, monthly, etc.)
- Shows detected frequency: "Auto-detected frequency: MONTHLY"
- Displays preview of first 10 prices
- Validates coverage against your investments

**Confirm the frequency:**
- If detected correctly → Leave it
- If wrong → Select correct frequency from dropdown

---

### Tab 2: Configuration

Click the **"⚙️ Configuration"** tab.

#### Step 2.1: Fund Information

**Fund Name:** Enter your fund's name (e.g., "Growth Fund I")
**Fund Manager:** Enter manager name (optional)

#### Step 2.2: Financial Parameters

Set your fund's terms using the sliders:

**Leverage Rate (%):**
- How much leverage as % of LP capital
- Default: 0%
- Range: 0% - 100%

**Cost of Capital (%):**
- Interest rate on leverage
- Default: 8%
- Range: 0% - 100%

**Management Fee Rate (%):**
- Annual management fee
- Default: 2%
- Range: 0% - 10%

**Carry Rate (%):**
- Carried interest / performance fee
- Default: 20%
- Range: 0% - 50%

**Hurdle Rate (%):**
- Minimum return before carry
- Default: 8%
- Range: 0% - 100%

#### Step 2.3: Simulation Parameters

**Number of Simulations:**
- How many scenarios to run
- Default: 10,000
- More = more accurate, but slower
- Recommended: 10,000 for analysis, 1,000 for testing

**Portfolio Size (Mean):**
- Average number of investments per portfolio
- Default: 10
- Based on your typical fund size

**Portfolio Size (Std Dev):**
- Variation in portfolio size
- Default: 2
- Higher = more variability in portfolio sizes

#### Step 2.4: Beta Forward Simulation Settings

**Simulation Horizon (Trading Days):**
- How far into the future to simulate
- Default: 2,520 days = 10 years
- 252 trading days = 1 year

**Number of Beta Paths:**
- How many market scenarios to generate
- Default: 1,000
- Each simulation samples one beta path

**Market Views:**

**Return Outlook:**
- **Pessimistic:** Historical return - 10%
- **Base:** Historical return (as-is)
- **Optimistic:** Historical return + 10%

**Volatility Confidence:**
- **Low:** 1.5× historical volatility (more uncertainty)
- **Medium:** 1.0× historical volatility (normal)
- **High:** 0.5× historical volatility (more certainty)

**Choose what makes sense for your market view!**

#### Step 2.5: Validate Configuration

At the bottom, you'll see either:
- ✅ **"✓ Configuration is valid"** → Good to go!
- ❌ **"Configuration errors:"** → Fix the listed issues

---

### Tab 3: Run Simulation

Click the **"▶️ Run Simulation"** tab.

#### Step 3.1: Review Summary

You'll see:
```
Ready to run 10,000 simulations with 45 investments
```

Verify this looks correct.

#### Step 3.2: Optional: Export Details

**"Export detailed investment and cash flow data for CSV analysis"**

- ✅ Check this if you want detailed CSV exports
- ⬜ Leave unchecked if you only need summary results
- **Note:** Checking this uses more memory

#### Step 3.3: Start Simulation

Click the big **"▶️ Run Simulation"** button.

#### Step 3.4: Watch Progress

You'll see **4 stages**:

**Stage 0/4: Decomposing historical beta from deals...**
- Separating alpha (skill) from beta (market)
- Shows: "✓ Stage 0: Decomposed 45 investments"

**Stage 1/4: Running alpha simulation (excess returns)...**
- Simulating manager skill component
- Progress bar: 0% → 100%
- Shows: "✓ Stage 1: Completed alpha simulation"

**Stage 2/4: Running beta forward simulation...**
- Simulating future market paths
- Shows: "✓ Stage 2: Generated 1,000 beta paths over 2,520 trading days"

**Stage 3/4: Reconstructing gross performance...**
- Combining alpha + beta
- Shows: "✓ Stage 3: Reconstructed 10,000 gross performance simulations"

**Stage 4/4: Reconstructing net performance...**
- Applying fees and costs
- Shows: "✓ Stage 4: Reconstructed 10,000 net performance simulations"

**Time:** Usually 10-30 seconds for 10,000 simulations

**When complete:**
```
✓ Completed simulation successfully
```

---

### Tab 4: Results

Click the **"📈 Results"** tab to see your results!

#### What You'll See

**Excel Export Button (Top):**
- Click "📥 Export Results to Excel" to download comprehensive report

**Stage 1: Alpha (Excess Returns)**
- Statistics on manager skill component
- MOIC and IRR distributions
- Histograms showing variability

**Stage 2: Beta Forward Simulation**
- Future market scenarios
- Price paths chart
- Terminal value statistics

**Stage 3: Gross Performance (Alpha × Beta)**
- Combined total returns before fees
- Beta attribution analysis
- Performance distributions

**Stage 4: Net Performance (After Costs)**
- Final returns after fees, carry, leverage
- Cost breakdown
- Net return distributions

---

## Understanding Your Results

### Key Metrics Explained

#### MOIC (Multiple on Invested Capital)
- **What it is:** How many times your money multiplied
- **Example:** 2.5x means $1 invested → $2.50 returned
- **1.0x** = break even
- **<1.0x** = loss
- **>1.0x** = profit

#### IRR (Internal Rate of Return)
- **What it is:** Annualized rate of return
- **Example:** 25% IRR means 25% per year
- **Compare to:** Public market returns (~10% historically)

#### Mean vs. Median
- **Mean:** Average of all simulations
- **Median:** Middle value (50th percentile)
- **If similar:** Distribution is symmetric
- **If different:** Distribution is skewed

#### Percentiles
- **5th Percentile:** Only 5% of scenarios were worse
- **95th Percentile:** Only 5% of scenarios were better
- **Range:** Shows best-case to worst-case outcomes

### Reading the Charts

#### Histograms
- **X-axis:** MOIC or IRR value
- **Y-axis:** Frequency (how often that outcome occurred)
- **Tall bars:** Common outcomes
- **Short bars:** Rare outcomes
- **Wider spread:** More uncertainty

**Red dashed line:** Mean (average)
**Green dashed line:** Median (middle value)

#### Beta Path Chart
- **Blue lines:** Individual market scenarios
- **Dark blue line:** Median path
- **Red dashed line:** 5th percentile (downside)
- **Green dashed line:** 95th percentile (upside)

### Interpreting Results

#### Healthy Results Typically Show:
- ✅ Median MOIC > 1.5x (profitable)
- ✅ Median IRR > 15% (exceeds public markets)
- ✅ 5th percentile MOIC > 1.0x (low downside risk)
- ✅ Narrow distribution (consistent performance)

#### Warning Signs:
- ⚠️ Median MOIC < 1.2x (low returns)
- ⚠️ 5th percentile MOIC < 0.5x (high downside risk)
- ⚠️ Very wide distribution (unpredictable)
- ⚠️ High negative scenarios (>20% of simulations losing money)

---

## Exporting Results

### Excel Export (Recommended)

**Click "📥 Export Results to Excel"**

**What you get:**
- Multi-sheet Excel workbook
- All charts embedded as images
- Summary statistics tables
- Professional formatting
- Ready to share with stakeholders

**Sheets included:**
1. **Executive Summary** - High-level overview
2. **Alpha Returns (Stage 1)** - Manager skill analysis
3. **Beta Simulation (Stage 2)** - Market scenario analysis
4. **Gross Performance (Stage 3)** - Combined returns
5. **Net Performance (Stage 4)** - Final returns after costs

**File name:** `[Fund_Name]_Results_[Timestamp].xlsx`

### CSV Export (Advanced)

If you checked "Export detailed data" before running:

**Investment Details CSV:**
- Every investment in every simulation
- Entry/exit dates, amounts, returns
- Beta attribution by investment

**Cash Flow Schedule CSV:**
- Day-by-day cash flows
- Capital calls and distributions
- Timing analysis

---

## Common Questions

### Q: How long does a simulation take?

**A:** Typically 10-30 seconds for 10,000 simulations. Factors:
- Number of simulations (more = slower)
- Number of historical investments (more = slower)
- Your computer speed

### Q: How many simulations should I run?

**A:**
- **1,000:** Quick testing, rough estimates
- **10,000:** Standard analysis (recommended)
- **100,000:** Very precise, publication-quality

**More simulations = more accurate results but takes longer**

### Q: What if I don't have beta price data?

**A:** You can still run simulations, but:
- Upload just your investment data
- Simulation will use historical returns directly
- You won't get alpha/beta decomposition
- Results will be simpler but still useful

### Q: Can I run multiple simulations with different settings?

**A:** Yes!
1. Run first simulation
2. Export results
3. Go back to Configuration tab
4. Change settings
5. Run again
6. Export new results
7. Compare the two Excel files

### Q: What data format does the application accept?

**A:**
- **Investment data:** CSV with 5 columns, no headers
- **Beta data:** CSV with 2 columns (date, price)
- **Dates:** YYYY-MM-DD, MM/DD/YYYY, or similar formats
- **Numbers:** Decimals (e.g., 2.5, 0.25) not percentages

### Q: Can I save my configuration?

**A:** Not currently, but you can:
- Take a screenshot of your configuration
- Keep notes on your settings
- Reenter settings for future runs

### Q: How do I close the application?

**A:**
1. Close the browser tab
2. Go to the black console window
3. Press `Ctrl + C` OR just close the window
4. Application stops

### Q: How do I restart the application?

**A:**
1. Close the application (see above)
2. Double-click desktop icon again
3. Wait ~5 seconds for browser to open
4. Application is running!

**Subsequent launches are FAST** (5-10 seconds) - no more package installation!

---

## Troubleshooting

### Issue: Application won't start

**Check:**
1. Is the console window open?
2. Did you wait 5-10 seconds for browser?
3. Try manually opening: `http://localhost:8501`

**If still not working:**
1. Close everything
2. Launch application again from desktop icon
3. Wait for console messages

### Issue: "Connection refused" in browser

**Problem:** Application hasn't started yet

**Fix:**
1. Check console window for errors
2. Wait 10-20 seconds
3. Refresh browser (F5)

### Issue: Browser doesn't open automatically

**Fix:**
1. Wait 10 seconds
2. Open browser manually
3. Go to: `http://localhost:8501`

### Issue: Charts not displaying

**Fix:**
1. Refresh browser (F5)
2. Check internet connection (needed for chart library)
3. Try different browser (Chrome, Edge, Firefox)

### Issue: Excel export fails

**Error:** "Missing dependencies: openpyxl, kaleido"

**This shouldn't happen** - but if it does:
1. Close application
2. Reinstall from installer
3. Wait for first-time setup to complete

### Issue: CSV upload fails

**Check your CSV file:**
- ✅ No headers in first row
- ✅ Exactly 5 columns (investment data) or 2 columns (beta data)
- ✅ Dates in recognizable format
- ✅ Numbers are numbers (not text)
- ✅ File saved as .csv (not .xlsx)

**Common fixes:**
1. Open CSV in Notepad to verify format
2. Make sure no extra commas
3. Check no special characters in names
4. Ensure dates are consistent format

### Issue: Simulation takes very long

**If running > 5 minutes:**
1. Check Number of Simulations (might be set too high)
2. Check Number of Beta Paths (might be set too high)
3. Try smaller test: 1,000 simulations first

**Recommended for normal use:**
- Simulations: 10,000
- Beta Paths: 1,000

### Issue: "Port 8501 is already in use"

**Problem:** Application already running (or crashed previously)

**Fix:**
1. Close all browser tabs with the application
2. Close all console windows
3. Open Task Manager (Ctrl + Shift + Esc)
4. Look for "python.exe" or "streamlit.exe"
5. End those processes
6. Launch application again

### Issue: Results look wrong / unexpected

**Checklist:**
1. ✅ Did you upload the right CSV file?
2. ✅ Is your data in the correct format?
3. ✅ Are MOIC values realistic? (e.g., 2.5 not 250)
4. ✅ Are IRR values as decimals? (e.g., 0.25 not 25)
5. ✅ Did the simulation complete all 4 stages?

**Try:**
- Review Data Import tab - check preview table
- Re-run simulation with same settings
- Compare results to expected range

---

## Tips for Success

### Best Practices

✅ **Start with test data** - Try 1,000 simulations first to verify settings
✅ **Review your data** - Check the preview table after upload
✅ **Save your settings** - Screenshot your configuration for reference
✅ **Export immediately** - Download Excel results right after simulation
✅ **Run multiple scenarios** - Try optimistic/base/pessimistic outlooks
✅ **Compare results** - Run with different horizons or portfolio sizes

### Data Quality Matters

Your results are only as good as your input data:
- ✅ Use actual historical returns (not estimates)
- ✅ Include both winners and losers
- ✅ Have at least 20+ historical investments
- ✅ Ensure dates are accurate
- ✅ Verify MOIC and IRR calculations

### Understanding Limitations

Monte Carlo simulation:
- ✅ Shows possible outcomes and probabilities
- ✅ Models historical patterns continuing
- ❌ Cannot predict black swan events
- ❌ Assumes past is representative of future
- ❌ Cannot account for strategy changes

**Use results to inform decisions, not make them automatically!**

---

## Getting Help

### If you get stuck:

1. **Read the error message** - Often tells you what's wrong
2. **Check this guide** - Search for your issue in Troubleshooting
3. **Try restarting** - Close and launch again
4. **Contact your administrator** - They can help with technical issues

### Useful Information to Provide When Asking for Help:

- What you were trying to do
- Error message (exact text)
- Screenshot of the problem
- What tab you were on
- Your configuration settings (screenshot)

---

## Next Steps

Now that you've completed your first simulation:

1. ✅ **Export your results** to Excel
2. ✅ **Review the distributions** and statistics
3. ✅ **Try different scenarios** (change outlook, horizon, etc.)
4. ✅ **Share with your team** - The Excel export is ready to present!
5. ✅ **Build confidence** - Run multiple simulations to understand variability

### Advanced Usage (Later)

Once comfortable with basics, explore:
- Different market outlooks (pessimistic vs. optimistic)
- Varying simulation horizons (5 years vs. 10 years)
- Testing different fee structures
- Comparing multiple funds
- Sensitivity analysis on key parameters

---

## Quick Reference Card

### To Launch Application:
Double-click desktop icon "Monte Carlo Fund Simulation"

### To Upload Data:
Tab 1: Data Import → Browse files → Select CSV → Open

### To Configure:
Tab 2: Configuration → Set parameters → Verify "✓ Configuration is valid"

### To Run:
Tab 3: Run Simulation → Click "▶️ Run Simulation" → Wait for 4 stages

### To View Results:
Tab 4: Results → Review charts and statistics

### To Export:
Tab 4: Results → Click "📥 Export Results to Excel" → Download

### To Close:
Close browser → Close console window (or Ctrl + C)

---

**Congratulations!** You're now ready to use the Monte Carlo Fund Simulation application.

**Questions?** Contact your administrator.

**Version:** 1.0.0
**Last Updated:** 2025-10-21
