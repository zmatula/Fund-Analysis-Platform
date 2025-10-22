# Alpha Simulation - Critical Clarifying Questions

**Status:** Awaiting Answers
**Priority:** Must answer before implementation

---

## 🔴 CRITICAL QUESTIONS (Must Answer First)

### Q1: Alpha Calculation Method ⭐ MOST IMPORTANT

You said: *"calculate the incremental irr and moic"*

**Which formula do you mean?**

#### Option A: Simple Subtraction (Additive)
```python
alpha_moic = investment_moic - beta_moic
alpha_irr = investment_irr - beta_irr
```

**Example:**
- Investment: 3.0x MOIC, 45% IRR
- Beta: 2.0x MOIC, 25% IRR
- **Alpha: 1.0x MOIC, 20% IRR**

#### Option B: Relative/Ratio (Multiplicative)
```python
alpha_moic = investment_moic / beta_moic
alpha_irr = ((1 + investment_irr) / (1 + beta_irr)) - 1
```

**Example:**
- Investment: 3.0x MOIC, 45% IRR
- Beta: 2.0x MOIC, 25% IRR
- **Alpha: 1.5x MOIC, 16% IRR**

**❓ Which interpretation is correct?**

---

### Q2: How to Use Alpha in Cash Flow Calculation

Once we have alpha_moic, how do we calculate exit proceeds?

#### Option A: Alpha as Direct Multiplier
```python
exit_amount = $1,000,000 × alpha_moic
```

**Problem:** If alpha = 0.5x, exit = $500K (you lost money!)

#### Option B: Alpha as Additive Return
```python
exit_amount = $1,000,000 × (1 + alpha_moic)
```

**Better:** If alpha = 0.5x, exit = $1.5M (you made 50% above market)

**❓ Which formula should we use?**

---

### Q3: What if Investment Entry/Exit Date Not in Beta Index?

**Scenario:**
- Investment entered on 2015-03-15
- Beta index only has prices for 2015-03-14 and 2015-03-16

**Options:**
- A) Use nearest prior date (2015-03-14)
- B) Linear interpolation between dates
- C) Error/skip this investment

**❓ Which approach?**

---

### Q4: What if Beta Data Doesn't Cover Investment Period?

**Scenario:**
- Investment: Entry 2010-01-01, Exit 2025-12-31
- Beta data: Only 2015-01-01 to 2025-10-19

**Options:**
- A) Use first/last available beta price
- B) Skip investment in alpha simulation
- C) Truncate holding period to beta coverage
- D) Show warning but allow calculation

**❓ Which approach?**

---

### Q5: What About Negative Alpha?

**Scenario:**
- Investment: 1.2x MOIC
- Beta: 1.8x MOIC
- Alpha: -0.6x (underperformed market)

**In simulation:**
- If using Option A (Q2): exit = $1M × -0.6 = -$600K ❌
- If using Option B (Q2): exit = $1M × (1 + (-0.6)) = $400K (lost 60%)

**❓ Is negative alpha expected/acceptable?**
**❓ Should we floor alpha at some minimum (e.g., -100%)?**

---

## 🟡 DESIGN QUESTIONS (Important but not blocking)

### Q6: Beta Index Naming
Should users be able to:
- Name their beta index? (e.g., "S&P 500", "NASDAQ", "Custom Benchmark")
- Upload multiple indices and select which to use?

### Q7: Results Display
Should the Results page show:
- Only alpha metrics?
- Both alpha and absolute side-by-side?
- Breakdown: Total Return = Beta Return + Alpha Return?

### Q8: Financial Engineering in Alpha Mode
Fees, carry, and leverage apply to:
- Alpha returns only?
- Still calculate on total capital but use alpha for returns?

**Clarify the logic.**

---

## 🟢 DATA QUALITY QUESTIONS (Good to know)

### Q9: Beta Data Validation
Should we enforce:
- Minimum data points? (e.g., ≥ 365 days)
- Maximum gap between dates? (e.g., ≤ 7 days)
- Price sanity checks? (e.g., no >50% daily moves)

### Q10: Investment Coverage Warning
Should we warn if:
- X% of investments fall outside beta date range?
- Show which investments can/cannot use alpha?

---

## Quick Decision Framework

**If you want the standard finance interpretation:**

**Recommended Answers:**
- **Q1:** Option A (Subtraction) - Standard in finance
- **Q2:** Option B (1 + alpha) - Prevents negative proceeds
- **Q3:** Option A (Prior date) - Simple and common
- **Q4:** Option D (Warning + allow) - User flexibility
- **Q5:** Yes, allow negative alpha with floor at -100%

**This would give results like:**
```
Investment: 2.5x MOIC, 35% IRR
Beta: 1.8x MOIC, 20% IRR
Alpha: 0.7x MOIC, 15% IRR

In simulation:
  Exit = $1M × (1 + 0.7) = $1.7M
  Interpretation: Made 70% above market return
```

---

## Example Calculation Walkthrough

Let me show both approaches with a real example:

**Investment Data:**
- Company: Zoom
- Entry: 2018-11-19
- Exit: 2020-03-23 (490 days)
- MOIC: 3.24x
- IRR: 202.27%

**Beta Index (S&P 500 example):**
- Price on 2018-11-19: $2,700
- Price on 2020-03-23: $2,237 (COVID crash!)
- Beta MOIC: 2237/2700 = 0.828x (loss!)
- Beta IRR: ((0.828)^(365/490)) - 1 = -13.3%

**Alpha Calculation:**

**Method A (Subtraction):**
- Alpha MOIC: 3.24 - 0.828 = **2.41x**
- Alpha IRR: 202.27% - (-13.3%) = **215.6%**

**Method B (Ratio):**
- Alpha MOIC: 3.24 / 0.828 = **3.91x**
- Alpha IRR: ((1 + 2.0227) / (1 + (-0.133))) - 1 = **270.7%**

**In Simulation (Method A + Option B for cash flow):**
- Investment: $1,000,000
- Alpha MOIC: 2.41x
- Exit: $1M × (1 + 2.41) = **$3,410,000**
- vs Absolute: $1M × 3.24 = $3,240,000

**❓ Does this match your intent?**

---

## How to Answer

Please respond with:
1. Q1: A or B
2. Q2: A or B
3. Q3: A, B, or C
4. Q4: A, B, C, or D
5. Q5: Your guidance

Or just say "use recommended" to go with the standard finance approach.

Once answered, I can implement immediately!
