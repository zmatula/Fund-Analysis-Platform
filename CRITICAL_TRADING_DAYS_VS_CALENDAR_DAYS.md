# CRITICAL: Trading Days vs Calendar Days

## THE BUG THAT MUST NEVER HAPPEN AGAIN

**Date:** 2025-10-20
**Severity:** CRITICAL
**Impact:** Caused simulation to end ~3 years early, showing wrong values at all intermediate dates

---

## What Went Wrong

### The Bug
In `beta_simulation.py` line 216, we were creating dates using:
```python
dates = pd.date_range(start=start_date + timedelta(days=1), periods=horizon_days, freq='D')
```

This created **2520 CALENDAR days** when `horizon_days=2520`.

### The Problem
- `horizon_days` represents **TRADING DAYS** (252 per year)
- 2520 trading days = 10 years of trading
- But 2520 calendar days = only ~6.9 calendar years
- This made the simulation end in August 2032 instead of October 2035
- All intermediate dates showed incorrect values

### The Symptom
- August 2032 (should be ~6.92 years into simulation) showed median ~253
- Expected: ~168 (for 6.92 years at 14.57% annual return)
- Actual: ~253 (terminal value for the wrongly shortened simulation)
- **Why:** August 2032 was row 2511 of 2520 - essentially the END of the simulation

---

## The Fix

```python
# Create DataFrame with dates spanning the correct time period
# horizon_days represents trading days, so convert to calendar time
# Approximately 252 trading days per 365.25 calendar days
calendar_years = horizon_days / 252
end_date = start_date + timedelta(days=int(calendar_years * 365.25))

# Create evenly-spaced dates spanning the full period
dates = pd.date_range(start=start_date + timedelta(days=1), end=end_date, periods=horizon_days)
paths_df = pd.DataFrame(paths, index=dates)
```

**Key insight:** We need to map trading days to the correct calendar time span.

---

## CRITICAL RULES FOR FUTURE WORK

### Rule 1: ALWAYS Distinguish Trading Days from Calendar Days

When you see a variable with "days" in the name, **IMMEDIATELY ASK:**
- Does this represent **trading days** (252/year) or **calendar days** (365.25/year)?
- Document this clearly in comments and variable names

### Rule 2: Use Explicit Naming

**GOOD:**
```python
horizon_trading_days = 2520  # 10 years × 252 trading days
horizon_calendar_days = int((horizon_trading_days / 252) * 365.25)
```

**BAD:**
```python
horizon_days = 2520  # Ambiguous! Trading or calendar?
```

### Rule 3: Financial Markets Use Trading Days for Returns

- Returns are annualized using 252 trading days per year
- When calculating `(1 + r) ** years`, use `years = trading_days / 252`
- But date ranges need to span the correct calendar time

### Rule 4: Conversion Formula

```python
# Trading days to calendar years
calendar_years = trading_days / 252

# Calendar years to trading days
trading_days = calendar_years * 252

# Calendar years to calendar days
calendar_days = calendar_years * 365.25
```

### Rule 5: Always Validate Intermediate Dates

When simulating forward, **NEVER** just check terminal values:
- Pick a known intermediate date (like we did with Aug 2032)
- Calculate expected value at that date
- Verify actual value matches expected
- This catches timeline errors immediately

---

## How This Bug Was Caught

1. User noticed August 2032 showed median ~253 instead of expected ~168
2. User's critical insight: "october of 2025 and august of 2032 isn't even a full 7 years later"
3. Added diagnostic to check row number for Aug 2032
4. Discovered Aug 2032 was row 2511 of 2520 - essentially the end
5. Realized simulation was only running ~6.9 years, not 10 years
6. Root cause: `freq='D'` creates calendar days, not trading days

---

## Testing Checklist for Future Beta Simulations

Before declaring a beta simulation correct, verify:

- [ ] Terminal date is correct (e.g., 2520 trading days from Oct 2025 should end in ~Oct 2035, not Aug 2032)
- [ ] Intermediate date values are reasonable (not showing terminal values too early)
- [ ] Row count matches horizon_days exactly
- [ ] Date span in years = horizon_days / 252 (approximately)
- [ ] Calendar year span ≈ (horizon_days / 252) × 365.25 / 365.25 = horizon_days / 252
- [ ] Example check: If horizon_days=2520, end date should be ~10 calendar years after start

---

## Example Validation

For a 10-year simulation starting October 25, 2025:

```python
horizon_trading_days = 2520
start_date = datetime(2025, 10, 25)

# Expected end date
calendar_years = 2520 / 252  # = 10.0 years
end_date = start_date + timedelta(days=int(10.0 * 365.25))
# Should be approximately October 2035

# Expected Aug 2032 value (6.92 years at 14.57% from 65.50)
years_to_aug_2032 = 6.92
expected_median = 65.50 * (1.1457 ** years_to_aug_2032)
# Should be approximately 168, NOT 255
```

---

## Why This Matters

Financial simulations are used for:
- Investment decisions
- Risk assessment
- Portfolio planning
- Client presentations

**A 3-year timeline error could lead to catastrophically wrong conclusions.**

This is why we validate intermediate dates, not just terminal statistics.

---

## Key Takeaway

**TRADING DAYS ≠ CALENDAR DAYS**

- 252 trading days = 1 year of returns
- 365.25 calendar days = 1 year of time
- When creating date ranges, convert trading days to calendar time
- Always validate intermediate dates, not just terminal values

**NEVER FORGET THIS LESSON.**

---

## CRITICAL: Backend vs Frontend Data Synchronization

### THE SECOND BUG - Module Caching Caused Backend/Frontend Disconnect

**Date:** 2025-10-20
**Severity:** CRITICAL
**Impact:** Wasted hours debugging because backend showed correct data but frontend showed stale cached data

### What Went Wrong

After fixing the trading days bug:
- Backend terminal output showed: `Aug 2032 median: 168.xx` ✓ CORRECT
- Frontend UI displayed: `Median: 253.xx` ✗ WRONG (old cached data)
- I kept saying "it's working!" based on backend diagnostics
- User kept saying "no it's not!" based on what they saw in the UI
- **MASSIVE disconnect and frustration**

### Root Cause

1. Python module caching (.pyc files) kept old code
2. Running Streamlit instances had old code loaded in memory
3. Clearing `__pycache__` folders wasn't enough
4. The processes needed to be **killed and restarted**

### The Cardinal Rule

**BACKEND AND FRONTEND MUST ALWAYS SHOW THE SAME DATA**

If they don't match:
- ❌ DO NOT trust backend diagnostics alone
- ❌ DO NOT assume the code is working
- ✅ The frontend is the source of truth (that's what the user sees!)
- ✅ Investigate why they're showing different values
- ✅ Kill and restart ALL processes to force code reload

---

## Mandatory Procedure for Code Updates

When you modify ANY backend simulation code:

### Step 1: Make Code Changes
- Update the Python source files
- Add version markers if needed
- Document changes

### Step 2: Clear All Caches
```bash
# Clear Python bytecode cache
python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if p.is_dir()]"
```

### Step 3: Kill ALL Running Instances
```bash
# DO NOT rely on existing instances to reload
# Kill them ALL
```

**Why:** Streamlit auto-reload is NOT sufficient for deep changes. Running processes have old code loaded in memory.

### Step 4: Start Fresh Instance
- Start a single new Streamlit instance
- DO NOT reuse old processes
- Wait for it to fully load

### Step 5: Verify Backend AND Frontend Match

**CRITICAL:** Always check BOTH:

1. **Backend (terminal output):**
   ```
   Aug 2032 median: 168.xx
   ```

2. **Frontend (UI display):**
   - Navigate to the results page
   - Check the same metric
   - Must show: `Median: 168.xx`

3. **If they don't match:**
   - 🚨 STOP IMMEDIATELY
   - Do NOT proceed
   - Do NOT claim it's working
   - Find out why they're different
   - Usually means: processes need to be killed

### Step 6: Document What You See

When reporting results to the user:
- ✅ "Backend shows X, frontend shows X - they match"
- ❌ "The median is X" (without specifying where you're seeing it)

---

## Rules for Debugging

### Rule 1: Trust the Frontend
- The frontend is what the user sees
- The frontend is the source of truth
- If frontend shows wrong data, the fix isn't working **period**

### Rule 2: Backend and Frontend Must Agree
- Check BOTH after every change
- If they disagree, something is cached
- Never declare success until they match

### Rule 3: When in Doubt, Nuke It
- Kill all processes
- Delete all `__pycache__` folders
- Delete `.pyc` files
- Start completely fresh

### Rule 4: Single Source of Truth
- Run ONE Streamlit instance at a time
- Don't have multiple instances on different ports
- Confusion about which instance is "the right one" = disaster

### Rule 5: Verify, Don't Assume
- After code changes, ALWAYS:
  1. Clear cache
  2. Kill processes
  3. Start fresh
  4. Check backend output
  5. Check frontend display
  6. **Verify they match**

---

## Checklist for Code Updates

Before declaring a fix is working:

- [ ] Code changes committed
- [ ] `__pycache__` folders deleted
- [ ] All Streamlit processes killed
- [ ] Started single fresh instance
- [ ] Backend terminal output checked
- [ ] Frontend UI display checked
- [ ] **Backend and frontend show SAME values**
- [ ] User confirmed they see correct values

**If any checkbox is unchecked, the fix is NOT verified.**

---

## Why This Matters

Time wasted in this session:
- ~1 hour of back-and-forth
- User repeatedly asking "are you seeing what I'm seeing?"
- User repeatedly asking "why are we seeing different numbers?"
- Frustration on both sides

**This was 100% preventable.**

The fix was actually working. The problem was cached code showing stale data in the frontend while I was looking at fresh data in the backend.

---

## Key Takeaway

**ALWAYS VERIFY BACKEND AND FRONTEND SHOW THE SAME DATA**

If they don't match:
1. Stop immediately
2. Kill all processes
3. Clear all caches
4. Start fresh
5. Verify again

**NEVER claim something is working based on backend diagnostics alone when the user is looking at a frontend UI.**

The frontend is reality. Backend diagnostics are just for debugging.

**NEVER FORGET THIS LESSON.**
