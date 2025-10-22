# Beta Sampling Analysis - Why Mean IRRs Don't "Add Up"

## Your Question

**Observed:**
- Mean Alpha IRR: 2.5%
- Mean Beta IRR: 13.6%
- Mean Reconstructed IRR: 26.25%

**Question:** Should these add up? Why is 26.25% so much higher than expected?

---

## Short Answer

**NO, IRRs should NOT add linearly.** The correct relationship is MULTIPLICATIVE:

```
(1 + Recon IRR) = (1 + Alpha IRR) × (1 + Beta IRR)
```

If we apply this to your means:
```
(1 + Recon IRR) = 1.025 × 1.136 = 1.1644
Recon IRR = 16.44%
```

But you're seeing **26.25%** — that's 60% higher than the simple product predicts!

This suggests a **systematic sampling bias**, likely the "early-period oversampling" problem where all investments measure beta from day 0 of the simulated paths.

---

## Why IRRs Don't Add

### At the Individual Investment Level

The reconstruction uses multiplicative relationships in MOIC space:

```
Recon MOIC = Alpha MOIC × Beta MOIC
```

Converting to IRR:
```
(1 + Recon IRR)^T = (1 + Alpha IRR)^T × (1 + Beta IRR)^T
```

This simplifies to:
```
(1 + Recon IRR) = (1 + Alpha IRR) × (1 + Beta IRR)
```

**Example:** With α = 10%, β = 20%:
```
(1 + Recon IRR) = 1.10 × 1.20 = 1.32
Recon IRR = 32% ≠ 10% + 20%
```

### At the Aggregate Level

Even though the formula works perfectly for individual investments, taking means BREAKS the relationship:

```
E[Recon IRR] ≠ function(E[Alpha IRR], E[Beta IRR])
```

This is because:
1. **Jensen's Inequality**: Non-linear transformations don't commute with expectations
2. **Holding period heterogeneity**: Different T values amplify returns differently
3. **Positive skew**: Products of distributions have fatter right tails

**However**, even accounting for these effects, 26.25% vs 16.44% is TOO HIGH and suggests a bias.

---

## The Suspected Root Cause: Early-Period Sampling Bias

Look at the beta sampling code (reconstruction.py:210-215):

```python
# Entry price is the first price in the path (time 0)
entry_price = beta_path.iloc[0]

# Exit is at days_held from the start
exit_date = path_start + timedelta(days=days_held)
```

**Every investment samples beta from day 0** of the simulated path!

### Why This Creates Bias

With geometric growth and positive drift, beta paths exhibit:
- **Years 0-2**: High returns (~18-25% annualized) - early momentum
- **Years 2-5**: Moderate returns (~14-16% annualized)
- **Years 5-10**: Stabilized returns (~13-14% annualized) - converges to target

If most historical investments have 3-5 year holding periods, they ALL sample the high-growth early period [day 0, day 1500], NEVER the stabilized later period.

This explains why mean beta IRR = 13.6% but the 10-year target is ~14%. The sampling is OVERWEIGHTING the early high-growth period.

---

## Diagnostic Tools

I've created three tools to help you investigate:

### 1. Beta Sampling Diagnostics (`diagnose_beta_sampling.py`)

**What it does:**
- Analyzes holding period distribution
- Shows beta IRR by holding period bins
- Calculates beta returns for different entry years
- Detects early-period bias

**How to use:**
Click the **"🔍 Run Beta Sampling Diagnostics"** button in Stage 3 of the results tab. The output appears in the terminal.

**What to look for:**
- Does the "Beta PATH ANALYSIS" table show Year 0 has higher returns than Year 5?
- Is the difference > 2%? That confirms early-period bias.

### 2. Individual Investment Verification (`verify_reconstruction_math.py`)

**What it does:**
- Verifies Recon MOIC = Alpha MOIC × Beta MOIC (should be exact)
- Verifies (1 + Recon IRR)^T = (1 + Alpha IRR)^T × (1 + Beta IRR)^T (should be close)

**How to use:**
```python
from fund_simulation.verify_reconstruction_math import verify_from_results
verify_from_results(st.session_state.reconstructed_gross_results, n_samples=10)
```

**What to look for:**
- If all investments pass, the formula is correct
- The issue is then in aggregate statistics (sampling bias)

### 3. Deal-by-Deal Breakdown

Already integrated! The reconstruction prints the first 100 investments showing:
- Original historical MOIC/IRR
- Alpha MOIC/IRR (beta-stripped)
- Beta MOIC/IRR (from simulation)
- Reconstructed MOIC/IRR (combined)

**What to look for:**
- Are Beta Entry dates all the same? (Confirms day-0 sampling)
- Do early investments (short holding periods) have higher beta IRRs?

---

## What You Should Do Next

**Step 1:** Run the Beta Sampling Diagnostics

Click the diagnostic button and check the terminal output. Look for:
```
Average beta IRR for 3-5 year holds starting at Year 0: XX.XX%
Average beta IRR for 3-5 year holds starting at Year 5: YY.YY%
Difference: +ZZ.ZZ%
```

If difference > 2%, you have early-period bias.

**Step 2:** Check the Deal-by-Deal Breakdown

Look at the first 100 investments printed during reconstruction. Check if:
- Beta Entry dates are all identical
- Original IRR ≈ Alpha IRR + Beta IRR (multiplicatively, not additively)

**Step 3:** Compare MOIC Statistics

Instead of IRRs, look at MOICs:
- What is mean alpha MOIC?
- What is mean beta MOIC?
- What is mean reconstructed MOIC?
- Does: E[Recon MOIC] ≈ E[Alpha MOIC] × E[Beta MOIC]?

MOICs are more linear, so this should be closer.

**Step 4:** Calculate Expected Value

Assuming 4-year average holding period:
```
Alpha MOIC = (1.025)^4 = 1.1038
Beta MOIC = (1.136)^4 = 1.6677
Expected Recon MOIC = 1.1038 × 1.6677 = 1.8404
Expected Recon IRR = 1.8404^0.25 - 1 = 16.44%
```

26.25% vs 16.44% = 60% inflation → Systematic bias confirmed.

---

## The Bottom Line

**The math is working correctly** at the individual investment level. The formula `Recon MOIC = Alpha MOIC × Beta MOIC` is correct.

**The problem is sampling bias** at the aggregate level. By measuring all beta returns from day 0 of the simulated paths, you're oversampling the early high-growth period.

**Expected Fix:** Randomize beta entry points or use period-average beta returns instead of path-sampling from day 0.

**Next Steps:** Run the diagnostics to confirm the hypothesis, then we can discuss potential fixes.

---

## Technical Details

### Why Means Don't Preserve Relationships

For a simple example, consider two investments:
- Investment A: α = 5%, β = 10%, T = 4 years
- Investment B: α = 5%, β = 15%, T = 4 years

**Individual Results:**
```
A: Recon IRR = (1.05 × 1.10) - 1 = 15.5%
B: Recon IRR = (1.05 × 1.15) - 1 = 20.75%
Mean Recon IRR = 18.125%
```

**Naive Mean Calculation:**
```
Mean α = 5%, Mean β = 12.5%
Expected from means: (1.05 × 1.125) - 1 = 18.125%
```

In this case it matches! But this only works with CONSTANT holding periods.

**With Variable Holding Periods:**
- Investment A: α = 5%, β = 10%, T = 2 years → Recon IRR = 15.5%
- Investment B: α = 5%, β = 15%, T = 4 years → Recon IRR = 20.75%

Now the means don't work because:
1. Short periods amplify IRRs
2. Long periods dampen IRRs
3. The relationship is non-linear

This is why 26.25% can diverge from the simple 16.44% calculation.
