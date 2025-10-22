# Handling Negative Alpha Below -100% - Analysis & Solutions

**Status:** Technical Analysis
**Date:** 2025-10-19

---

## Problem Statement

**User Requirements:**
- Allow alpha MOIC < -100% (e.g., -2.3x)
- Allow alpha IRR < -100% (e.g., -250%)
- Use: `exit_amount = $1,000,000 × alpha_moic`

**Example Scenario:**
```
Investment: 0.5x MOIC, -30% IRR (lost 50%)
Beta: 3.0x MOIC, +80% IRR (gained 200%)
Alpha: 0.5 - 3.0 = -2.5x MOIC
       -0.30 - 0.80 = -110% IRR

In simulation:
  Initial: -$1,000,000 (investment outflow)
  Exit: $1,000,000 × (-2.5) = -$2,500,000 (NEGATIVE cash flow!)
```

**Economic Interpretation:**
"This investment underperformed the beta benchmark by so much that on a relative basis, you not only lost your principal, but would need to pay an additional $1.5M to match beta's performance."

---

## Mathematical Implications

### 1. ⚠️ Negative Exit Cash Flows

**Issue:**
```python
cash_flows = {
    1000: $2,000,000,   # Two good investments
    1000: -$2,500,000,  # One terrible investment (same exit day)
}

Aggregated:
cash_flows[1000] = $2M + (-$2.5M) = -$500,000 ❌ NET NEGATIVE
```

**Impact:**
- Cash flow dictionaries can have negative values
- Some days might have net outflows instead of inflows
- `total_returned = sum(cash_flows.values())` can be negative

### 2. 🔴 IRR Calculation Breaks

**Current IRR Formula (Newton-Raphson):**
```python
NPV = -initial_investment + Σ(cash_flow_i / (1 + r)^(days_i/365))
```

**With negative cash flows:**
```
NPV = -$10M + $2M/(1+r)^(1000/365) + (-$2.5M)/(1+r)^(1000/365) + ...
    = -$10M + (-$500K)/(1+r)^(1000/365) + ...
```

**Problems:**
- Multiple IRR solutions possible (polynomial with multiple roots)
- Newton-Raphson may not converge
- May converge to wrong solution
- IRR may not exist mathematically

**Example of Multiple IRRs:**
```
Year 0: -$1,000
Year 1: +$3,000
Year 2: -$2,000

This has TWO IRRs: ~-9.6% and ~216%
```

### 3. 🟡 Financial Engineering Complications

**Carry Calculation:**
```python
hurdle_return = $15M × (1 + 0.08 × 3.5) = $19.2M
total_returned = -$5M (negative!)
excess_return = max(0, -$5M - $19.2M) = 0
carry = 0 × 0.20 = $0 ✓ Already handled by max(0, ...)
```

**Net Returns:**
```python
total_returned = -$5M
leverage_cost = $1.4M
management_fees = $1.05M
carry = $0

net_returned = -$5M - $1.4M - $1.05M - $0 = -$7.45M
net_moic = -$7.45M / $10M = -0.745x (lost 74.5%)
```

**This is fine!** Negative MOIC is interpretable.

### 4. 🟢 Statistics Still Work

**Summary statistics with negative values:**
```python
moics = [2.5, 1.8, -0.5, 3.2, -1.2, 1.5]

mean_moic = 1.22x ✓
median_moic = 1.65x ✓
std_dev = 1.8x ✓
min = -1.2x ✓
max = 3.2x ✓
percentiles = all work ✓
```

**Histograms still work** - just extend into negative territory.

---

## Proposed Solutions

### ✅ **SOLUTION 1: Robust IRR Calculation (RECOMMENDED)**

**Problem:** Newton-Raphson may not converge with negative cash flows

**Fix:** Implement fallback strategy

```python
def calculate_irr_robust(cash_flows: Dict[int, float], initial_investment: float) -> float:
    """
    Calculate IRR with robust handling of negative cash flows.

    Returns:
        IRR as decimal, or -0.9999 if calculation fails
    """
    # Try Newton-Raphson (existing method)
    try:
        rate = calculate_irr_newton_raphson(cash_flows, initial_investment)

        # Verify solution (NPV should be near zero)
        npv = verify_npv(rate, cash_flows, initial_investment)
        if abs(npv) < 1000:  # Reasonable tolerance
            return rate
    except:
        pass

    # Fallback 1: Try different initial guesses
    for initial_guess in [-0.5, 0.0, 0.1, 0.5, 1.0]:
        try:
            rate = calculate_irr_newton_raphson(
                cash_flows, initial_investment, initial_guess=initial_guess
            )
            npv = verify_npv(rate, cash_flows, initial_investment)
            if abs(npv) < 1000:
                return rate
        except:
            continue

    # Fallback 2: Bisection method (slower but more robust)
    try:
        rate = calculate_irr_bisection(cash_flows, initial_investment)
        return rate
    except:
        pass

    # Fallback 3: Return floor value
    # If total cash flows are negative, return -99.99%
    total_cash_flows = sum(cash_flows.values())
    if total_cash_flows < initial_investment:
        return -0.9999  # Lost everything
    else:
        return 0.0  # Break even
```

**Advantages:**
- Handles most negative cash flow scenarios
- Graceful degradation when IRR doesn't exist
- Returns interpretable value

**Implementation:**
- Add bisection method as backup
- Add NPV verification
- Return sentinel value (-0.9999) when fails

---

### ✅ **SOLUTION 2: Warning System**

**Track problematic simulations:**

```python
@dataclass
class SimulationResult:
    # ... existing fields ...

    # New fields for diagnostics
    has_negative_cash_flows: bool = False
    irr_converged: bool = True
    negative_total_returned: bool = False
```

**Display warnings:**
```python
# In results summary
problematic_sims = sum(1 for r in results if not r.irr_converged)
if problematic_sims > 0:
    st.warning(f"{problematic_sims} simulations ({problematic_sims/len(results):.1%}) "
               f"had IRR calculation issues due to negative cash flows. "
               f"IRR values for these are approximate.")

negative_returns = sum(1 for r in results if r.total_returned < 0)
if negative_returns > 0:
    st.info(f"{negative_returns} simulations ({negative_returns/len(results):.1%}) "
            f"had negative total returns (underperformed beta significantly).")
```

---

### ✅ **SOLUTION 3: Add Modified IRR (MIRR) Option**

**Alternative metric for problematic cases:**

```python
def calculate_mirr(
    cash_flows: Dict[int, float],
    initial_investment: float,
    finance_rate: float = 0.10,
    reinvest_rate: float = 0.10
) -> float:
    """
    Calculate Modified IRR which handles negative cash flows better.

    MIRR assumes:
    - Negative cash flows are financed at finance_rate
    - Positive cash flows are reinvested at reinvest_rate

    This always produces a single answer.
    """
    max_day = max(cash_flows.keys())
    years = max_day / 365.0

    # Future value of positive cash flows (reinvested)
    fv_positive = 0
    for day, cf in cash_flows.items():
        if cf > 0:
            remaining_years = (max_day - day) / 365.0
            fv_positive += cf * ((1 + reinvest_rate) ** remaining_years)

    # Present value of negative cash flows (financed)
    pv_negative = initial_investment  # Initial investment is negative
    for day, cf in cash_flows.items():
        if cf < 0:
            years_from_start = day / 365.0
            pv_negative += abs(cf) / ((1 + finance_rate) ** years_from_start)

    # MIRR calculation
    if pv_negative > 0 and fv_positive > 0:
        mirr = (fv_positive / pv_negative) ** (1 / years) - 1
    else:
        mirr = -0.9999

    return mirr
```

**Display both IRR and MIRR:**
- Standard IRR (may fail with negative flows)
- MIRR (always works, different interpretation)

---

### ✅ **SOLUTION 4: Cap Negative Alpha (OPTIONAL)**

**If extreme negative alphas are unrealistic:**

```python
def calculate_alpha_metrics(
    investment_moic: float,
    investment_irr: float,
    beta_moic: float,
    beta_irr: float,
    min_alpha_moic: float = -5.0  # Floor at -500%
) -> Tuple[float, float]:
    """
    Calculate alpha with optional floor.
    """
    alpha_moic = investment_moic - beta_moic
    alpha_irr = investment_irr - beta_irr

    # Apply floor if needed
    if min_alpha_moic is not None:
        alpha_moic = max(alpha_moic, min_alpha_moic)

    return (alpha_moic, alpha_irr)
```

**Make floor configurable:**
- Default: -5.0x (-500%)
- User can adjust in Configuration
- Or disable entirely (None)

---

### ✅ **SOLUTION 5: Alternative Simulation Mode (SAFEST)**

**Provide two alpha simulation types:**

#### **Type A: "Alpha Cash Flow Simulation"** (What we've discussed)
- Directly uses alpha for cash flows
- Can have negative proceeds
- IRR may not converge
- More volatile results
- Economically represents "relative portfolio returns"

#### **Type B: "Alpha Return Analysis"** (Safer alternative)
- Run normal absolute return simulation
- Calculate beta return for each simulation
- Compute alpha = absolute - beta POST-SIMULATION
- IRR always converges (using absolute cash flows)
- Alpha shown separately in results

**UI would show:**
```
Simulation Type: [Absolute] [Alpha Cash Flow] [Alpha Analysis]

Alpha Analysis: Calculates alpha metrics from absolute returns
                (Recommended for beginners)

Alpha Cash Flow: Builds portfolio using alpha returns directly
                 (Advanced - may produce negative cash flows)
```

---

## Recommended Implementation Strategy

**Phase 1: Implement Robust IRR (Required)**
- Add bisection method fallback
- Add NPV verification
- Add failure handling
- Test with negative cash flows

**Phase 2: Add Warning System (Required)**
- Track convergence status
- Show % of problematic simulations
- Explain negative returns

**Phase 3: Add MIRR Option (Nice to have)**
- Calculate MIRR alongside IRR
- Display both metrics
- User can choose which to prioritize

**Phase 4: Add Alpha Floor Config (Optional)**
- Allow user to set min_alpha_moic
- Default to None (no floor)
- Explain implications in UI

**Phase 5: Add Alternative Mode (Future)**
- "Alpha Analysis" mode for safer results
- Side-by-side comparison
- Educational for users

---

## Testing Strategy

**Create test cases with extreme alphas:**

**Test Case 1: Moderate Negative Alpha**
```
Investment: 1.5x MOIC, 20% IRR
Beta: 2.0x MOIC, 25% IRR
Alpha: -0.5x MOIC, -5% IRR
Exit: $1M × -0.5 = -$500K
Expected: IRR converges, negative MOIC
```

**Test Case 2: Extreme Negative Alpha**
```
Investment: 0.3x MOIC, -40% IRR
Beta: 3.0x MOIC, 80% IRR
Alpha: -2.7x MOIC, -120% IRR
Exit: $1M × -2.7 = -$2.7M
Expected: IRR may not converge, use fallback
```

**Test Case 3: Mixed Portfolio**
```
10 investments:
- 7 with positive alpha (+0.5x to +2.0x)
- 3 with negative alpha (-0.3x to -1.5x)
Expected: Some negative cash flows, overall positive return
```

**Test Case 4: All Negative Alpha**
```
Portfolio where all alphas are negative
Expected: Negative total return, fees still apply, no carry
```

---

## Final Recommendation

**Implement Solutions 1 + 2 immediately:**
1. ✅ Robust IRR with fallbacks
2. ✅ Warning system for users

**Consider Solution 3 (MIRR) if IRR issues persist**

**Skip Solution 4 (floor) - user wants full range**

**Save Solution 5 (alternative mode) for future enhancement**

This allows full negative alpha while maintaining mathematical stability.

---

## Questions for User

None! Requirements are clear. Ready to implement once beta interpolation strategy is confirmed.

---

**Next:** Confirm beta data interpolation approach (see separate document).
