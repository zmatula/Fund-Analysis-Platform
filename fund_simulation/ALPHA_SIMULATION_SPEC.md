# Alpha Simulation Feature - Speckit Specification

**Version:** 1.0 (Draft)
**Created:** 2025-10-19
**Status:** Requirements Analysis & Clarification

---

## Table of Contents

1. [Feature Overview](#feature-overview)
2. [Data Model Analysis](#data-model-analysis)
3. [Architecture Changes](#architecture-changes)
4. [Data Flow Mapping](#data-flow-mapping)
5. [Calculation Specifications](#calculation-specifications)
6. [UI/UX Changes](#uiux-changes)
7. [Clarifying Questions](#clarifying-questions)
8. [Implementation Plan](#implementation-plan)

---

## Feature Overview

### Purpose
Enable users to measure "alpha" - the excess return of investments above a benchmark (beta) index. This allows fund managers to understand whether their returns came from:
- **Beta** (market movement) - what would have been achieved by holding the index
- **Alpha** (skill/selection) - excess returns above the index

### High-Level Flow
```
1. User uploads beta pricing data (dates + prices)
2. System validates beta data
3. User runs "Alpha Simulation" (in addition to existing "Return Simulation")
4. For each investment selected:
   a. Calculate beta IRR/MOIC over same holding period
   b. Calculate alpha (incremental) IRR/MOIC
   c. Use alpha metrics in simulation instead of absolute returns
5. Display alpha-adjusted results
```

### Key Concept
**Alpha Calculation:**
```
Alpha IRR = Investment IRR - Beta IRR (over same period)
Alpha MOIC = Investment MOIC - Beta MOIC (over same period)
```

---

## Data Model Analysis

### New Data Structure: BetaPricing

```python
@dataclass
class BetaPrice:
    """
    Single beta index price observation.
    """
    date: datetime
    price: float

    def validate(self) -> List[str]:
        errors = []
        if self.price <= 0:
            errors.append(f"Price must be positive (got {self.price})")
        return errors


@dataclass
class BetaPriceIndex:
    """
    Complete beta pricing index with validation and lookups.
    """
    prices: List[BetaPrice]  # Sorted by date
    data_hash: str = ""

    @property
    def start_date(self) -> datetime:
        return self.prices[0].date if self.prices else None

    @property
    def end_date(self) -> datetime:
        return self.prices[-1].date if self.prices else None

    def validate(self) -> List[str]:
        errors = []

        if len(self.prices) < 2:
            errors.append("Beta index must have at least 2 price points")

        # Check sorted order
        for i in range(len(self.prices) - 1):
            if self.prices[i].date >= self.prices[i + 1].date:
                errors.append(f"Dates must be in ascending order (problem at index {i})")

        # Check for duplicates
        dates = [p.date for p in self.prices]
        if len(dates) != len(set(dates)):
            errors.append("Duplicate dates found")

        return errors

    def get_price_on_date(self, date: datetime) -> Optional[float]:
        """
        Get price on exact date or nearest prior date.

        Returns None if date is before index start.
        """
        # Implementation details TBD
        pass

    def calculate_return(self, entry_date: datetime, exit_date: datetime) -> Tuple[float, float]:
        """
        Calculate MOIC and IRR for holding beta from entry to exit.

        Returns:
            Tuple of (beta_moic, beta_irr)
        """
        # Implementation details TBD
        pass
```

### Modified Configuration Model

```python
@dataclass
class SimulationConfiguration:
    # ... existing fields ...

    # New fields for alpha simulation
    simulation_type: str = "absolute"  # "absolute" or "alpha"
    beta_index_hash: str = ""  # Hash of beta pricing data
```

---

## Architecture Changes

### Component Modifications Required

```
┌─────────────────────────────────────────────────────────────┐
│                    MODIFIED COMPONENTS                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. DATA IMPORT LAYER (NEW)                                 │
│     - beta_import.py (NEW FILE)                             │
│       • parse_beta_csv()                                    │
│       • validate_beta_prices()                              │
│                                                               │
│  2. MODELS LAYER (MODIFIED)                                 │
│     - models.py                                              │
│       • Add BetaPrice class                                 │
│       • Add BetaPriceIndex class                            │
│       • Modify SimulationConfiguration                      │
│                                                               │
│  3. CALCULATORS LAYER (NEW)                                 │
│     - calculators.py                                         │
│       • calculate_beta_return() (NEW)                       │
│       • calculate_alpha_metrics() (NEW)                     │
│                                                               │
│  4. SIMULATION ENGINE (MODIFIED)                            │
│     - simulation.py                                          │
│       • Modify run_single_simulation()                      │
│       • Add alpha adjustment logic                          │
│                                                               │
│  5. UI LAYER (MODIFIED)                                     │
│     - app.py                                                 │
│       • Add beta upload section in Data Import              │
│       • Add simulation type selector in Configuration       │
│       • Modify results display for alpha metrics            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### File Structure Changes

```
fund_simulation/
├── fund_simulation/
│   ├── models.py              [MODIFIED - add beta models]
│   ├── calculators.py         [MODIFIED - add beta/alpha calcs]
│   ├── data_import.py         [EXISTING]
│   ├── beta_import.py         [NEW - beta CSV parsing]
│   ├── simulation.py          [MODIFIED - add alpha mode]
│   └── statistics.py          [EXISTING - no changes]
├── app.py                     [MODIFIED - add beta upload & alpha UI]
└── requirements.txt           [EXISTING - no new dependencies]
```

---

## Data Flow Mapping

### Flow 1: Beta Data Upload

```
┌─────────────┐
│ User uploads│
│  beta CSV   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│ parse_beta_csv()        │
│ - Read 2 columns        │
│ - Parse dates           │
│ - Parse prices          │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Create BetaPrice objects│
│ - One per row           │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Create BetaPriceIndex   │
│ - Sort by date          │
│ - Validate              │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Display validation      │
│ results to user         │
│ - Date range            │
│ - Price count           │
│ - Any errors            │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Store in session state  │
│ Enable alpha simulation │
└─────────────────────────┘
```

### Flow 2: Alpha Simulation Execution

```
┌────────────────────────────────────────────────────────────────┐
│              FOR EACH SIMULATION ITERATION                      │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Generate Portfolio & Select Investments                     │
│     [SAME AS EXISTING]                                          │
│                                                                  │
│  2. For each selected investment:                              │
│     ┌──────────────────────────────────────────────────────┐  │
│     │ a. Get investment entry_date (from original data)    │  │
│     │ b. Calculate days_held (from MOIC/IRR as before)     │  │
│     │ c. Calculate exit_date = entry_date + days_held      │  │
│     └──────────────────┬───────────────────────────────────┘  │
│                        │                                        │
│                        ▼                                        │
│     ┌──────────────────────────────────────────────────────┐  │
│     │ d. Calculate Beta Performance                         │  │
│     │    - Get beta price on entry_date                     │  │
│     │    - Get beta price on exit_date                      │  │
│     │    - Calculate beta_moic = exit_price / entry_price   │  │
│     │    - Calculate beta_irr (using same formula)          │  │
│     └──────────────────┬───────────────────────────────────┘  │
│                        │                                        │
│                        ▼                                        │
│     ┌──────────────────────────────────────────────────────┐  │
│     │ e. Calculate Alpha                                    │  │
│     │    - alpha_moic = investment_moic - beta_moic         │  │
│     │    - alpha_irr = investment_irr - beta_irr            │  │
│     └──────────────────┬───────────────────────────────────┘  │
│                        │                                        │
│                        ▼                                        │
│     ┌──────────────────────────────────────────────────────┐  │
│     │ f. Use ALPHA metrics for cash flow calculation       │  │
│     │    - exit_amount = $1M × (1 + alpha_moic)             │  │
│     │    - Continue with existing simulation logic          │  │
│     └────────────────────────────────────────────────────────┘  │
│                                                                  │
│  3. Aggregate cash flows, apply financial engineering          │
│     [SAME AS EXISTING]                                          │
│                                                                  │
│  4. Calculate net IRR and MOIC                                 │
│     [SAME AS EXISTING]                                          │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Calculation Specifications

### Beta Return Calculation

**Input:**
- Entry date: Date investment was made
- Exit date: Entry date + days_held
- Beta price index

**Process:**

```python
def calculate_beta_return(
    entry_date: datetime,
    exit_date: datetime,
    beta_index: BetaPriceIndex
) -> Tuple[float, float]:
    """
    Calculate MOIC and IRR for holding beta index.

    Returns:
        Tuple of (beta_moic, beta_irr)
    """
    # Step 1: Get entry price
    entry_price = beta_index.get_price_on_date(entry_date)
    if entry_price is None:
        # Entry date before beta index starts
        # QUESTION: What to do here?
        return (1.0, 0.0)  # Assume no return?

    # Step 2: Get exit price
    exit_price = beta_index.get_price_on_date(exit_date)
    if exit_price is None:
        # Exit date after beta index ends
        # QUESTION: What to do here?
        return (1.0, 0.0)  # Assume no return?

    # Step 3: Calculate MOIC
    beta_moic = exit_price / entry_price

    # Step 4: Calculate IRR
    days_held = (exit_date - entry_date).days
    # Using same formula: MOIC = (1 + IRR)^(days/365)
    # Therefore: IRR = (MOIC^(365/days)) - 1
    if days_held > 0:
        beta_irr = (beta_moic ** (365.0 / days_held)) - 1
    else:
        beta_irr = 0.0

    return (beta_moic, beta_irr)
```

### Alpha Calculation

```python
def calculate_alpha_metrics(
    investment_moic: float,
    investment_irr: float,
    beta_moic: float,
    beta_irr: float
) -> Tuple[float, float]:
    """
    Calculate alpha (excess) returns.

    Returns:
        Tuple of (alpha_moic, alpha_irr)
    """
    # QUESTION: Is this the right formula?
    # Option A: Simple subtraction
    alpha_moic = investment_moic - beta_moic
    alpha_irr = investment_irr - beta_irr

    # Option B: Relative calculation
    # alpha_moic = investment_moic / beta_moic - 1
    # alpha_irr = ((1 + investment_irr) / (1 + beta_irr)) - 1

    return (alpha_moic, alpha_irr)
```

### Modified Cash Flow Calculation

```python
# In run_single_simulation():

for investment in selected_investments:
    days_held = calculate_holding_period(investment.moic, investment.irr)

    if config.simulation_type == "alpha" and beta_index is not None:
        # Calculate exit date
        exit_date = investment.entry_date + timedelta(days=days_held)

        # Calculate beta return over same period
        beta_moic, beta_irr = calculate_beta_return(
            investment.entry_date,
            exit_date,
            beta_index
        )

        # Calculate alpha
        alpha_moic, alpha_irr = calculate_alpha_metrics(
            investment.moic,
            investment.irr,
            beta_moic,
            beta_irr
        )

        # Use alpha for exit amount
        # QUESTION: Should we use alpha_moic or (1 + alpha_moic)?
        exit_amount = investment_amount * (1 + alpha_moic)
    else:
        # Existing absolute return logic
        exit_amount = investment_amount * investment.moic

    # Aggregate cash flows
    if days_held in cash_flows:
        cash_flows[days_held] += exit_amount
    else:
        cash_flows[days_held] = exit_amount
```

---

## UI/UX Changes

### Page 1: Data Import (MODIFIED)

**New Section: Beta Index Upload**

```
┌─────────────────────────────────────────────────────────────┐
│ Import Historical Investment Data                           │
│ [Upload CSV button]                                         │
│ ✓ Loaded 107 investments                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Import Beta Index (Optional)                                │
│                                                              │
│ Upload beta pricing data to enable alpha simulations.       │
│                                                              │
│ CSV Format (NO headers):                                    │
│   Column 1: Date (YYYY-MM-DD, MM/DD/YYYY, etc.)            │
│   Column 2: Price (closing price)                          │
│                                                              │
│ [Upload Beta CSV button]                                    │
│                                                              │
│ ✓ Loaded 5,000 price points                                │
│   Date Range: 2010-01-01 to 2025-10-19                     │
│   Coverage: 15.8 years                                      │
└─────────────────────────────────────────────────────────────┘
```

### Page 2: Configuration (MODIFIED)

**New Option: Simulation Type**

```
┌─────────────────────────────────────────────────────────────┐
│ Simulation Type                                             │
│                                                              │
│ ○ Absolute Returns (default)                               │
│   Simulate based on actual investment returns               │
│                                                              │
│ ○ Alpha Returns (requires beta index)                      │
│   Simulate excess returns above beta benchmark             │
│   ⚠ Beta index must be uploaded first                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Page 4: Results (MODIFIED)

**Modified Display for Alpha Mode**

```
If simulation_type == "alpha":
  - Label results as "Alpha MOIC" and "Alpha IRR"
  - Add explanation text:
    "These results show excess returns above the beta benchmark.
     Alpha MOIC of 1.5x means 1.5x above market returns."
  - Optionally show comparison to absolute returns
```

---

## Clarifying Questions

### Critical Questions (MUST ANSWER)

**Q1: Alpha Calculation Method**
```
User said: "adjust the irr and moic by calculating the incremental irr and moic"

Which formula is correct?

Option A (Simple Subtraction):
  alpha_moic = investment_moic - beta_moic
  alpha_irr = investment_irr - beta_irr

  Example: Investment 3.0x, Beta 2.0x → Alpha = 1.0x

Option B (Relative/Ratio):
  alpha_moic = investment_moic / beta_moic
  alpha_irr = ((1 + investment_irr) / (1 + beta_irr)) - 1

  Example: Investment 3.0x, Beta 2.0x → Alpha = 1.5x

Which interpretation is correct?
```

**Q2: Alpha Cash Flow Calculation**
```
When using alpha in simulation, what's the exit amount?

Option A: Use alpha directly as multiplier
  exit_amount = $1M × alpha_moic

  Problem: If alpha_moic = 0.5x, exit is only $500K (loss!)

Option B: Use (1 + alpha) as multiplier
  exit_amount = $1M × (1 + alpha_moic)

  Better: If alpha_moic = 0.5x, exit is $1.5M (gain)

Which is intended?
```

**Q3: Beta Date Interpolation**
```
What if the exact entry/exit date isn't in beta index?

Option A: Use nearest prior date (last observation carried forward)
Option B: Linear interpolation between dates
Option C: Raise error if exact date not found

Which approach?
```

**Q4: Beta Coverage Gaps**
```
What if investment period extends beyond beta data?

Scenario: Investment entry 2000-01-01, exit 2025-12-31
          Beta data only goes to 2025-10-19

Option A: Use last available beta price for exit
Option B: Skip this investment in alpha simulation
Option C: Extrapolate beta price (not recommended)
Option D: Truncate holding period to beta coverage

Which approach?
```

**Q5: Negative Alpha Handling**
```
What if alpha is negative?

Example: Investment 1.2x MOIC, Beta 1.5x MOIC → Alpha = -0.3x

In simulation:
  - If alpha_moic = -0.3x, exit_amount could be $700K (loss)
  - Is this intended behavior?
  - Should we floor alpha at some minimum?
```

### Design Questions

**Q6: Beta Index Name/Identifier**
```
Should we:
- Allow user to name the beta index? (e.g., "S&P 500", "NASDAQ")
- Store multiple beta indices?
- Display beta index name in results?
```

**Q7: Results Comparison**
```
Should results page show:
- Only alpha results?
- Both alpha and absolute results side-by-side?
- Breakdown showing: Investment Return = Beta Return + Alpha Return
```

**Q8: Financial Engineering in Alpha Mode**
```
In alpha simulation, fees/carry/leverage apply to:
- Alpha returns only? (seems right)
- Total absolute returns? (confusing)

Clarify the sequence.
```

### Data Quality Questions

**Q9: Beta Price Validation**
```
Should we validate:
- Minimum number of data points? (e.g., ≥ 365 days)
- Maximum gap between dates? (e.g., no more than 7 days)
- Price reasonableness? (e.g., no negative, no >50% daily moves)
```

**Q10: Investment Coverage Check**
```
Should we warn user if:
- Some investments fall outside beta date range?
- Show % of investments that can use alpha calculation?
```

---

## Calculation Examples

### Example 1: Basic Alpha Calculation

**Investment:**
- Entry: 2015-01-01
- Exit: 2018-01-01 (1,096 days)
- MOIC: 3.0x
- IRR: 44.22%

**Beta Index:**
- Price on 2015-01-01: $100
- Price on 2018-01-01: $150
- Beta MOIC: 1.5x
- Beta IRR: 14.47%

**Alpha (assuming Option A - subtraction):**
- Alpha MOIC: 3.0 - 1.5 = 1.5x
- Alpha IRR: 44.22% - 14.47% = 29.75%

**Alpha (assuming Option B - relative):**
- Alpha MOIC: 3.0 / 1.5 = 2.0x
- Alpha IRR: ((1 + 0.4422) / (1 + 0.1447)) - 1 = 26.0%

### Example 2: Simulation Cash Flow

**Absolute Mode:**
```
Investment: $1,000,000
MOIC: 3.0x
Exit: $3,000,000
```

**Alpha Mode (Option A - subtraction, alpha = 1.5x):**
```
Investment: $1,000,000
Alpha MOIC: 1.5x
Exit: $1,000,000 × 1.5 = $1,500,000  ❌ Seems low!
```

**Alpha Mode (Option B - 1 + alpha, alpha = 1.5x):**
```
Investment: $1,000,000
Alpha MOIC: 1.5x
Exit: $1,000,000 × (1 + 1.5) = $2,500,000  ✓ More sensible
```

---

## Implementation Plan

### Phase 1: Beta Data Import (2-3 hours)
- [ ] Create `beta_import.py`
- [ ] Implement `parse_beta_csv()`
- [ ] Create BetaPrice and BetaPriceIndex models
- [ ] Add validation logic
- [ ] Write unit tests

### Phase 2: Beta Calculation Engine (2-3 hours)
- [ ] Implement `calculate_beta_return()`
- [ ] Implement date lookup with interpolation
- [ ] Implement `calculate_alpha_metrics()`
- [ ] Write unit tests
- [ ] Test with real S&P 500 data

### Phase 3: Simulation Integration (2-3 hours)
- [ ] Modify `run_single_simulation()` to support alpha mode
- [ ] Add beta_index parameter
- [ ] Implement conditional logic for alpha vs absolute
- [ ] Update SimulationConfiguration model
- [ ] Test both modes

### Phase 4: UI Integration (3-4 hours)
- [ ] Add beta upload section to Data Import tab
- [ ] Add simulation type selector to Configuration tab
- [ ] Modify Results display for alpha mode
- [ ] Add helper text and warnings
- [ ] Test complete workflow

### Phase 5: Testing & Validation (2-3 hours)
- [ ] Create test beta index (e.g., S&P 500 2010-2025)
- [ ] Run alpha simulation with Lead Edge data
- [ ] Verify calculations manually for sample investments
- [ ] Document expected behavior
- [ ] Update README

**Total Estimated Time:** 11-16 hours

---

## Risk Assessment

### High Risk
- ⚠️ **Calculation correctness** - Alpha formula interpretation critical
- ⚠️ **Date alignment** - Beta dates may not match investment dates exactly
- ⚠️ **Negative alpha handling** - Could produce unexpected results

### Medium Risk
- ⚡ **Beta data coverage** - May not span all investment dates
- ⚡ **Data quality** - Beta prices from user could be incomplete/wrong
- ⚡ **UI complexity** - Adding mode switcher might confuse users

### Low Risk
- ✓ **Performance** - Beta lookup is O(log n), shouldn't impact speed
- ✓ **Backward compatibility** - Absolute mode unchanged, alpha is additive

---

## Open Issues for Discussion

1. **Alpha Formula** - Need definitive answer on subtraction vs ratio
2. **Cash Flow Calculation** - How to apply alpha in exit amount
3. **Date Interpolation** - Strategy for non-exact date matches
4. **Coverage Gaps** - Behavior when beta data insufficient
5. **Result Presentation** - Show alpha only, or alpha + absolute?
6. **Multiple Beta Indices** - Future: allow multiple benchmarks?

---

## Success Criteria

Implementation is complete when:
- [ ] User can upload beta CSV and see validation
- [ ] Beta data is stored and accessible
- [ ] Alpha simulation produces mathematically correct results
- [ ] UI clearly distinguishes alpha vs absolute modes
- [ ] Edge cases handled gracefully (gaps, negative alpha, etc.)
- [ ] Documentation updated with alpha mode instructions
- [ ] Tests verify alpha calculations against known examples

---

**Next Steps:**
1. **Answer clarifying questions** (especially Q1-Q5)
2. **Approve calculation methodology**
3. **Begin Phase 1 implementation**

---

**End of Specification**
