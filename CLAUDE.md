# CLAUDE.md - Guide for Future Claude Instances

**Last Updated:** 2025-10-20
**Purpose:** Comprehensive guide for future Claude Code instances working in this Monte Carlo fund simulation repository

---

## Quick Start Commands

### Running the Streamlit Application

```bash
# Navigate to the fund_simulation directory
cd "C:\Users\ZacharyMatula\Code Projects\Private Fund Simulation\fund_simulation"

# Run the Streamlit app
streamlit run app.py
```

Default port: 8501
Alternative ports if needed: 8502, 9000, etc.

### Clearing Python Cache (CRITICAL AFTER CODE CHANGES)

```bash
# Clear all __pycache__ directories
python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]"
```

**IMPORTANT:** After ANY code change to Python files, you MUST:
1. Clear all `__pycache__` directories
2. Kill ALL running Streamlit instances
3. Start ONE fresh Streamlit instance
4. Verify backend terminal output matches frontend UI display

See: **CRITICAL_BACKEND_FRONTEND_SYNC.md** for the mandatory protocol.

### Killing Streamlit Processes

```bash
# Find all Streamlit processes
tasklist | findstr streamlit

# Kill specific process by PID (replace XXXX with actual PID)
taskkill /PID XXXX /F
```

---

## High-Level Architecture

This application is a **Monte Carlo fund simulation engine** for modeling future fund performance. It has evolved to support two distinct simulation modes with a sophisticated beta decomposition methodology.

### Two Simulation Modes

#### Mode 1: Past Performance (Original)
- Uses historical total returns directly
- Draws from actual investment MOIC/IRR without decomposition
- Simple resampling with replacement
- No market exposure modeling

#### Mode 2: Deconstructed Performance (Beta-Aware)
**This is the primary mode and where most complexity exists.**

Follows a 5-stage pipeline:

1. **Beta Decomposition (Historical)**
   - Takes historical investments with total returns
   - Uses a beta price index (e.g., S&P 500, Russell 2000)
   - Separates each investment's return into:
     - **Beta component**: Market exposure (`G_beta = G_mkt^β`)
     - **Alpha component**: Excess return (`G_alpha = G_total / G_beta`)
   - File: `fund_simulation/data_import.py::decompose_historical_beta()`

2. **Alpha Simulation**
   - Builds portfolios by randomly selecting from **alpha-only** investments
   - Calculates alpha-only MOIC/IRR for each simulated portfolio
   - NO beta at this stage - pure manager skill modeling
   - File: `fund_simulation/simulation.py::run_monte_carlo_simulation()`

3. **Beta Forward Simulation**
   - Generates future market (beta) price paths using constant-growth methodology
   - Takes user's forward-looking view: outlook (pessimistic/base/optimistic) and confidence (low/medium/high)
   - Produces N paths spanning the simulation horizon
   - **CRITICAL:** Uses trading days (252/year) for returns but calendar time for dates
   - File: `fund_simulation/beta_simulation.py::simulate_beta_forward()`

4. **Performance Reconstruction**
   - For each simulated portfolio, combines alpha + beta paths
   - Multiplicative reconstruction: `Total Return = Alpha × (Beta^β)`
   - Samples one beta path per portfolio
   - File: `fund_simulation/reconstruction.py::reconstruct_performance_with_beta_paths()`

5. **Results Display**
   - Shows terminal statistics (median MOIC, median IRR)
   - Displays beta attribution analysis
   - Plots beta path chart over time
   - Consistency checks verify terminal values match expected returns
   - File: `app.py` (Streamlit UI)

---

## CRITICAL: Trading Days vs Calendar Days

**THIS IS THE #1 BUG THAT MUST NEVER HAPPEN AGAIN**

See: **CRITICAL_TRADING_DAYS_VS_CALENDAR_DAYS.md**

### The Rule

- **Trading days** = 252 per year (used for return calculations)
- **Calendar days** = 365.25 per year (used for date spans)
- When you see `horizon_days` in this codebase, it means **TRADING DAYS**

### The Bug (Fixed 2025-10-20)

In `beta_simulation.py`, we were using:
```python
# WRONG - creates 2520 CALENDAR days (~6.9 years)
dates = pd.date_range(start=start_date, periods=2520, freq='D')
```

This caused a 10-year simulation (2520 trading days) to end in August 2032 instead of October 2035.

### The Fix

```python
# CORRECT - converts trading days to calendar time
calendar_years = horizon_days / 252  # 2520 / 252 = 10 years
end_date = start_date + timedelta(days=int(calendar_years * 365.25))
dates = pd.date_range(start=start_date + timedelta(days=1), end=end_date, periods=horizon_days)
```

### Validation Checklist

Before declaring a beta simulation correct:
- [ ] Terminal date is correct (e.g., 2520 trading days from Oct 2025 → Oct 2035, NOT Aug 2032)
- [ ] Intermediate date values are reasonable
- [ ] Date span in years ≈ horizon_days / 252
- [ ] Example: If horizon_days=2520, end date should be ~10 calendar years after start

**ALWAYS validate intermediate dates, not just terminal values.**

---

## CRITICAL: Backend/Frontend Synchronization

**THIS IS THE #2 BUG THAT MUST NEVER HAPPEN AGAIN**

See: **CRITICAL_BACKEND_FRONTEND_SYNC.md**

### The Cardinal Rule

**BACKEND AND FRONTEND MUST ALWAYS SHOW THE SAME DATA**

If they show different values, **THE FIX IS NOT WORKING**.

### What Happened (2025-10-20)

After fixing the trading days bug:
- Backend terminal: `Aug 2032 median: 168.xx` ✓
- Frontend UI: `Median: 253.xx` ✗
- Result: ~1 hour wasted in confusion

**Cause:** Stale Python modules cached in running Streamlit processes.

### Mandatory Checklist After ANY Code Change

```
[ ] 1. Made code changes
[ ] 2. Cleared ALL __pycache__ directories
[ ] 3. Killed ALL running Streamlit instances
[ ] 4. Started ONE fresh Streamlit instance
[ ] 5. Ran simulation in the UI
[ ] 6. Checked backend terminal output
[ ] 7. Checked frontend UI display
[ ] 8. VERIFIED THEY SHOW IDENTICAL VALUES
[ ] 9. User confirmed they see the correct values
```

**If all 9 boxes aren't checked, the fix is NOT verified.**

### 5 Critical Rules

1. **Trust the Frontend** - Frontend = what user sees = source of truth
2. **Backend and Frontend Must Agree** - If different → something cached
3. **When in Doubt, Nuke Everything** - Kill processes, clear caches, start fresh
4. **Run ONE Instance Only** - Multiple instances = confusion
5. **Verify, Don't Assume** - Auto-reload is NOT sufficient

### Before Reporting to User

**DON'T SAY:**
- ❌ "It's working!"
- ❌ "The median is 168"

**DO SAY:**
- ✅ "Backend terminal shows 168, frontend UI shows 168 - they match"
- ✅ "Please confirm you see [X] in the UI"

---

## Key Files and Their Roles

### Core Simulation Files

#### `fund_simulation/models.py`
- Data models: `Investment`, `BetaPriceIndex`, `BetaPrice`
- Model validation logic
- Field definitions and types

#### `fund_simulation/calculators.py`
- Core financial calculations
- `calculate_holding_period()`: days = 365 × ln(MOIC) / ln(1 + IRR)
- `calculate_irr()`: Newton-Raphson IRR solver
- Cash flow calculations

#### `fund_simulation/data_import.py`
- CSV parsing: `parse_csv_file()`
- **CRITICAL:** `decompose_historical_beta()` - Stage 1 of deconstructed pipeline
  - Separates historical returns into alpha and beta
  - Uses multiplicative decomposition: G_total = G_alpha × G_beta^β
  - Returns alpha-only investments + diagnostics

#### `fund_simulation/beta_import.py`
- Beta price index CSV parsing
- Validates and loads historical market data
- Supports daily, weekly, monthly, quarterly, annual frequencies

#### `fund_simulation/simulation.py`
- `run_monte_carlo_simulation()` - Stage 2 of deconstructed pipeline
- Core Monte Carlo engine
- Portfolio construction with replacement
- Financial engineering: leverage, fees, carry, hurdle
- Returns alpha-only simulation results

#### `fund_simulation/beta_simulation.py` ⚠️ CRITICAL
- **Version:** `v2.1_exact_moments_FIXED_TRADING_DAYS_BUG`
- `calculate_historical_statistics()`: Extracts annualized return and volatility from beta index
- `simulate_beta_forward()` - Stage 3 of deconstructed pipeline
  - Generates future beta price paths
  - Uses constant-growth methodology (each path = single constant daily return)
  - Applies outlook modifier (±10%) and confidence modifier (0.5×, 1.0×, 1.5×)
  - **Uses symmetric antithetic pairs** to ensure EXACT mean, median, stdev
  - ⚠️ **MUST correctly convert trading days to calendar time for date ranges**

**Key Section in beta_simulation.py (lines 215-233):**
```python
# CRITICAL: Create DataFrame with dates spanning the correct time period
#
# horizon_days represents TRADING DAYS (252 per year), NOT calendar days!
#
# See CRITICAL_TRADING_DAYS_VS_CALENDAR_DAYS.md for full documentation
calendar_years = horizon_days / 252
end_date = start_date + timedelta(days=int(calendar_years * 365.25))

# Create evenly-spaced dates spanning the full period
dates = pd.date_range(start=start_date + timedelta(days=1), end=end_date, periods=horizon_days)
paths_df = pd.DataFrame(paths, index=dates)
```

#### `fund_simulation/reconstruction.py`
- `reconstruct_performance_with_beta_paths()` - Stage 4 of deconstructed pipeline
- Combines alpha simulation results with beta forward paths
- Multiplicative reconstruction: Total MOIC = Alpha MOIC × (Beta MOIC^β)
- Samples one beta path per portfolio
- Recalculates IRR from reconstructed MOIC

#### `fund_simulation/statistics.py`
- Statistical aggregation functions
- Percentile calculations
- Summary statistics

### UI and Display

#### `app.py` (Streamlit Application)
- 4-page workflow: Upload Data → Configure → Run → Results
- Stage 5 of deconstructed pipeline: Results display
- **Lines 978-1036:** Comprehensive debugging diagnostics (can be enabled when debugging)
- **Lines 1067-1105:** Terminal Value Statistics with consistency checks
- **Consistency checks:**
  - Terminal median vs target return (should match within tolerance)
  - Terminal median vs actual beta return from reconstruction (should match)

**Key UI Sections:**
- Investment data table
- Beta attribution analysis (shows alpha, beta, total breakdown)
- Beta Forward Simulation Chart (price paths over time)
- Terminal Value Statistics (annualized returns, not raw prices)

### Test and Diagnostic Files

#### `fund_simulation/verify_reconstruction_math.py`
- Validates that Total = Alpha × Beta^β decomposition is exact
- Checks round-trip accuracy (decompose → reconstruct → compare)
- Use this to verify mathematical integrity after changes

#### `fund_simulation/diagnose_beta_sampling.py`
- Diagnoses beta forward simulation sampling
- Verifies exact moments (mean, median, stdev)
- Moved to top-level for easy access

#### `fund_simulation/diagnose_reporting.py`
- Diagnoses reporting and aggregation issues
- Moved to top-level for easy access

### Documentation Files (MUST READ)

#### ⚠️ CRITICAL_TRADING_DAYS_VS_CALENDAR_DAYS.md
**READ THIS FIRST if working on beta simulation**
- Documents the trading days bug and fix
- 5 Critical Rules for future work
- Testing checklist
- Example validation scenarios
- Includes backend/frontend sync section

#### ⚠️ CRITICAL_BACKEND_FRONTEND_SYNC.md
**READ THIS FIRST if making ANY code changes**
- Protocol for verifying backend/frontend match
- 9-point mandatory checklist
- 5 critical debugging rules
- Communication guidelines

#### TECHNICAL_SPECIFICATION.md
- Complete algorithmic specification
- Mathematical formulas
- Edge case handling

#### ARCHITECTURE_AND_DATA_FLOW.md
- System architecture
- Data flow diagrams
- Component interactions

#### API_DOCUMENTATION.md
- Complete API reference for all modules
- Function signatures and descriptions

---

## Common Tasks

### Task 1: Update Beta Simulation Logic

**Files to modify:**
- `fund_simulation/beta_simulation.py`

**CRITICAL STEPS:**
1. Read CRITICAL_TRADING_DAYS_VS_CALENDAR_DAYS.md
2. Make your changes
3. Update version marker: `__BETA_SIMULATION_VERSION__ = "vX.X_description"`
4. Clear `__pycache__`: `python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]"`
5. Kill ALL Streamlit instances
6. Start ONE fresh instance: `streamlit run app.py`
7. Run simulation in UI
8. Check backend terminal output
9. Check frontend UI display
10. **VERIFY THEY MATCH** (values, dates, everything)
11. Ask user to confirm

**Testing:**
- Pick an intermediate date (e.g., Aug 2032 for a 2025-2035 simulation)
- Calculate expected value at that date
- Verify actual value matches
- Verify terminal date is correct (e.g., 2520 trading days → 10 calendar years)

### Task 2: Update Alpha Simulation Logic

**Files to modify:**
- `fund_simulation/simulation.py`
- Possibly `fund_simulation/calculators.py` if changing financial calculations

**Steps:**
1. Make your changes
2. Run test: `python test_alpha_simulation.py` (if exists)
3. Follow standard backend/frontend verification protocol
4. Check that beta reconstruction still works correctly

### Task 3: Update Decomposition Logic

**Files to modify:**
- `fund_simulation/data_import.py::decompose_historical_beta()`

**Steps:**
1. Make your changes
2. Run verification: `python fund_simulation/verify_reconstruction_math.py`
3. Verify round-trip accuracy: decompose → reconstruct → should equal original
4. Follow standard backend/frontend verification protocol

### Task 4: Update UI Display

**Files to modify:**
- `app.py`

**CRITICAL:**
- Any changes to how data is displayed MUST be verified in the actual UI
- Backend print statements do NOT count as verification
- User must see the correct values in the browser

**Steps:**
1. Make your changes
2. Follow standard backend/frontend verification protocol
3. Pay special attention to:
   - Chart Y-axis labels (clarify price vs return)
   - Consistency checks (terminal median vs target)
   - Date ranges (verify correct calendar span)

### Task 5: Debug Inconsistent Values

**When user reports UI showing wrong values:**

1. **DO NOT assume your code is working based on backend output alone**
2. Read CRITICAL_BACKEND_FRONTEND_SYNC.md
3. Add comprehensive debugging diagnostics (see app.py lines 978-1036 for example)
4. Check:
   - What data is being used for the chart?
   - What data is being used for terminal statistics?
   - Do they come from the same source?
   - Are dates correct (trading vs calendar)?
   - Is there any caching issue?
5. Clear cache, kill processes, start fresh
6. Verify backend and frontend match
7. Ask user to confirm

---

## Code Patterns and Conventions

### Version Markers

When making significant changes to core simulation files, update version markers:

```python
# In beta_simulation.py
__BETA_SIMULATION_VERSION__ = "v2.1_exact_moments_FIXED_TRADING_DAYS_BUG"
```

This helps track what code is running and when bugs were introduced/fixed.

### Trading Days Calculations

**ALWAYS use this pattern:**

```python
# For return calculations
trading_years = horizon_days / 252
annual_return = (terminal_moic) ** (1 / trading_years) - 1

# For date ranges
calendar_years = horizon_days / 252
end_date = start_date + timedelta(days=int(calendar_years * 365.25))
dates = pd.date_range(start=start_date, end=end_date, periods=horizon_days)
```

**NEVER use:**
```python
# WRONG - confuses trading days with calendar days
dates = pd.date_range(start=start_date, periods=horizon_days, freq='D')
```

### Reproducibility

All simulations use fixed random seeds:
- Default seed: `42`
- Ensures identical results for same inputs
- Symmetric antithetic pairs in beta simulation ensure exact moments

### Error Handling

- IRR = -1.0 is adjusted to -0.9999 (avoid log(0) in holding period calculation)
- MOIC = 0 is allowed (total loss)
- Dates outside beta index coverage skip investment with warning

---

## Mathematical Core Concepts

### Beta Decomposition (Multiplicative)

For a historical investment:
```
G_total = Total gross return (MOIC)
G_mkt = Market return over same period from beta index
G_beta = G_mkt^β (where β = beta exposure coefficient)
G_alpha = G_total / G_beta (alpha component)
```

### Performance Reconstruction

For a simulated portfolio:
```
Alpha MOIC (from simulation)
Beta MOIC (from sampled path)
Total MOIC = Alpha MOIC × (Beta MOIC^β)
```

### Constant-Growth Beta Paths

Each beta path:
1. Draw a terminal annualized return from N(r_target, σ_target)
2. Calculate total multiple needed: `(1 + terminal_return)^years`
3. Find constant daily return: `daily_r = total_multiple^(1/horizon_days) - 1`
4. Compound for `horizon_days`: `price[t] = price[t-1] × (1 + daily_r)`

### Symmetric Antithetic Pairs

To ensure EXACT mean, median, and stdev:
```python
# Generate magnitudes from half-normal
a = abs(rng.standard_normal(n/2))
# Create symmetric pairs
z = concatenate([-a, a])  # mean=0, median=0 exactly
# If odd, add exact 0
if odd: z = concatenate([z, [0]])
# Shuffle and rescale to unit variance
z = z / sqrt(mean(z**2))
# Transform
return mean + sigma * z
```

This guarantees:
- Mean = target mean (exactly)
- Median = target median (exactly)
- Stdev = target stdev (exactly)

---

## Debugging Workflow

### Problem: Simulation Results Look Wrong

1. **Check intermediate dates, not just terminal values**
   - Pick a known intermediate date
   - Calculate expected value
   - Compare to actual
   - If wrong, likely a timeline issue (trading vs calendar days)

2. **Verify data source**
   - Add print statements showing what data is being used
   - Trace from source (beta_paths DataFrame) to display (chart/statistics)
   - Look for unit conversions, sampling, filtering

3. **Check consistency across UI sections**
   - Terminal statistics
   - Chart data
   - Beta attribution analysis
   - These should all harmonize

4. **Enable comprehensive diagnostics**
   - See app.py lines 978-1036 for example
   - Show: DataFrame shape, dates, terminal values, calculations, version

5. **Verify backend/frontend match**
   - Always check BOTH
   - If different → caching issue
   - Clear cache, kill processes, start fresh

### Problem: Backend Shows Different Values Than Frontend

**THIS IS A CRITICAL ERROR - STOP IMMEDIATELY**

1. Do NOT proceed
2. Do NOT claim it's working
3. Read CRITICAL_BACKEND_FRONTEND_SYNC.md
4. Clear ALL `__pycache__` directories
5. Kill ALL Streamlit processes
6. Start ONE fresh instance
7. Verify again

### Problem: Dates Are Wrong

1. Check if using trading days vs calendar days correctly
2. Read CRITICAL_TRADING_DAYS_VS_CALENDAR_DAYS.md
3. Verify: `calendar_years = horizon_days / 252`
4. Verify: `end_date = start_date + timedelta(days=int(calendar_years * 365.25))`
5. Check actual terminal date in DataFrame
6. Calculate expected terminal date and compare

---

## User Preferences

Based on this session, the user has strong preferences:

### Code Style
- **Remove verbose output** - User repeatedly requested removal of unnecessary diagnostics
- Only show diagnostics when actively debugging
- Keep terminal output clean and focused

### Debugging Approach
- Add comprehensive diagnostics when debugging
- Show data source, tracebacks, version info
- Include consistency checks
- Remove diagnostics once issue is resolved

### Documentation
- Create comprehensive documentation for critical bugs
- Document lessons learned to prevent recurrence
- Be explicit about what went wrong and why

### Communication
- Always verify backend AND frontend match
- Report what you see in both places
- Ask user to confirm they see the same values
- Don't claim something is working based on backend alone

### Frustration Points
- Backend/frontend disconnect (NEVER again)
- Claiming something works when user sees different values
- Not being thorough in verification
- Timeline bugs (trading vs calendar days)

---

## Common Pitfalls to Avoid

### Pitfall 1: Trusting Backend Diagnostics Alone
**Wrong:** "The backend shows 168, so it's working!"
**Right:** "Backend shows 168, frontend shows 168 - they match. Can you confirm?"

### Pitfall 2: Assuming Streamlit Auto-Reload Works
**Wrong:** Making code changes and assuming Streamlit reloaded correctly
**Right:** Clear cache, kill processes, start fresh, verify

### Pitfall 3: Confusing Trading Days with Calendar Days
**Wrong:** `pd.date_range(periods=2520, freq='D')` for 10 years
**Right:** Convert to calendar time, then create date range

### Pitfall 4: Only Checking Terminal Values
**Wrong:** "Terminal median is 255, looks good!"
**Right:** Check intermediate dates too - verify Aug 2032 shows ~168, not ~255

### Pitfall 5: Not Asking User to Confirm
**Wrong:** Reporting results without user verification
**Right:** Show what you see, ask user to confirm they see the same

---

## Quick Reference

### File Locations
```
fund_simulation/
├── fund_simulation/
│   ├── models.py              # Data models
│   ├── calculators.py         # Core calculations
│   ├── data_import.py         # CSV + beta decomposition (Stage 1)
│   ├── beta_import.py         # Beta index loading
│   ├── simulation.py          # Monte Carlo alpha simulation (Stage 2)
│   ├── beta_simulation.py     # Beta forward simulation (Stage 3) ⚠️
│   ├── reconstruction.py      # Performance reconstruction (Stage 4)
│   └── statistics.py          # Statistical aggregation
├── app.py                     # Streamlit UI (Stage 5)
├── CRITICAL_TRADING_DAYS_VS_CALENDAR_DAYS.md  ⚠️ READ FIRST
├── CRITICAL_BACKEND_FRONTEND_SYNC.md          ⚠️ READ FIRST
└── verify_reconstruction_math.py              # Validation tool
```

### Key Constants
- Trading days per year: **252**
- Calendar days per year: **365.25**
- Default random seed: **42**

### Conversion Formulas
```python
trading_years = horizon_days / 252
calendar_years = horizon_days / 252  # Same value, different context
calendar_days = calendar_years * 365.25
```

### Verification Checklist
- [ ] Backend terminal output checked
- [ ] Frontend UI display checked
- [ ] Values match exactly
- [ ] Dates span correct calendar time
- [ ] Intermediate dates show reasonable values
- [ ] Terminal date is correct
- [ ] User confirmed

---

## Final Notes

This codebase has undergone significant debugging to fix two critical bugs:

1. **Trading days vs calendar days** - Fixed 2025-10-20
2. **Backend/frontend synchronization** - Documented 2025-10-20

Both bugs wasted significant time and caused user frustration. The comprehensive documentation (CRITICAL_*.md files) and this CLAUDE.md file exist to ensure **these bugs never happen again**.

### Golden Rules

1. **TRADING DAYS ≠ CALENDAR DAYS** - Never forget this
2. **BACKEND = FRONTEND** - If they differ, something is cached
3. **VERIFY, DON'T ASSUME** - Check both backend and frontend every time
4. **ASK USER TO CONFIRM** - Don't claim success without user verification
5. **READ THE CRITICAL DOCS** - They exist for a reason

### When in Doubt

1. Read CRITICAL_TRADING_DAYS_VS_CALENDAR_DAYS.md
2. Read CRITICAL_BACKEND_FRONTEND_SYNC.md
3. Clear cache, kill processes, start fresh
4. Verify backend and frontend match
5. Ask user to confirm

**Good luck, future Claude instance. Learn from our mistakes.**

---

**Document Version:** 1.0
**Last Updated:** 2025-10-20
**Critical Bugs Fixed:** 2 (trading days, backend/frontend sync)
