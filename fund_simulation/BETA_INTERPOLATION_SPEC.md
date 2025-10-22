# Beta Data Interpolation Strategy - Specification

**Status:** Confirmation Required
**Date:** 2025-10-19

---

## User Requirements Summary

**Q3 Answer:** "Interpolate linearly between points... user may upload daily, monthly, quarterly or annual beta prices depending on data availability... when interpolating assume this represents the midpoint of the period."

**Q4 Answer:** "Beta data needs to cover the whole period. If a data point needed is not available then throw an error."

---

## Interpolation Strategy

### Midpoint Assumption

**User uploads monthly data:**
```csv
2015-07-01, 100.00
2015-08-01, 105.00
```

**Interpretation:**
- July price (100.00) represents **mid-July** (2015-07-15)
- August price (105.00) represents **mid-August** (2015-08-15)

### Linear Interpolation Between Midpoints

**To get price for 2015-07-25:**

```
Step 1: Determine midpoints
  P1 = 100.00 at 2015-07-15 (mid-July)
  P2 = 105.00 at 2015-08-15 (mid-August)

Step 2: Calculate days
  Date needed: 2015-07-25
  Days from P1: 10 days (July 15 → July 25)
  Days P1 to P2: 31 days (July 15 → Aug 15)

Step 3: Linear interpolation
  weight = 10 / 31 = 0.3226
  price = 100 + (105 - 100) × 0.3226 = 101.61
```

---

## Frequency Detection

**Upon CSV upload, detect frequency and ask user to confirm:**

```python
def detect_frequency(dates: List[datetime]) -> str:
    """
    Detect the frequency of beta price data.

    Returns: "daily", "weekly", "monthly", "quarterly", "annual", or "irregular"
    """
    if len(dates) < 2:
        return "insufficient_data"

    # Calculate gaps between consecutive dates
    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
    median_gap = np.median(gaps)

    if median_gap <= 2:
        return "daily"
    elif 5 <= median_gap <= 9:
        return "weekly"
    elif 25 <= median_gap <= 35:
        return "monthly"
    elif 85 <= median_gap <= 95:
        return "quarterly"
    elif 360 <= median_gap <= 370:
        return "annual"
    else:
        return "irregular"
```

**UI Confirmation Dialog:**
```
┌─────────────────────────────────────────────────────────────┐
│ Beta Price Frequency Detected: MONTHLY                      │
│                                                              │
│ We detected 120 price points with ~30 days between each.   │
│                                                              │
│ Frequency: ● Monthly  ○ Quarterly  ○ Annual  ○ Other       │
│                                                              │
│ For interpolation, we will assume each price represents     │
│ the MIDPOINT of the period:                                 │
│                                                              │
│   Example: Price on 2015-07-01 represents mid-July         │
│            (2015-07-15)                                     │
│                                                              │
│ [ Confirm ] [ Cancel ]                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Midpoint Calculation by Frequency

### Daily Data
```
Date in CSV: 2015-07-15
Assumed midpoint: 2015-07-15 (same day - no adjustment needed)
```

### Weekly Data
```
Date in CSV: 2015-07-06 (Monday)
Assumed midpoint: 2015-07-09 (Thursday, +3 days)
```

### Monthly Data
```
Date in CSV: 2015-07-01
Assumed midpoint: 2015-07-15 (~middle of month)

Note: Different months have different midpoints
  Jan (31 days): 1st → 16th (+15 days)
  Feb (28 days): 1st → 15th (+14 days)
  Apr (30 days): 1st → 15th (+14 days)
```

### Quarterly Data
```
Date in CSV: 2015-07-01 (Q3 start)
Assumed midpoint: 2015-08-15 (middle of Q3)
  Q3 = Jul/Aug/Sep = 92 days
  Midpoint = 46 days from July 1st
```

### Annual Data
```
Date in CSV: 2015-01-01
Assumed midpoint: 2015-07-02 (middle of year)
  Year = 365 days
  Midpoint = 182.5 days from Jan 1st
```

---

## Implementation: Midpoint Calculation

```python
def calculate_midpoint(date: datetime, frequency: str) -> datetime:
    """
    Calculate the midpoint of the period represented by this date.

    Args:
        date: Date from CSV
        frequency: "daily", "weekly", "monthly", "quarterly", "annual"

    Returns:
        Datetime representing midpoint of period
    """
    if frequency == "daily":
        return date

    elif frequency == "weekly":
        # Assume date is Monday, midpoint is Thursday (+3 days)
        return date + timedelta(days=3)

    elif frequency == "monthly":
        # Calculate middle of month
        year, month = date.year, date.month

        # Get last day of month
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)

        last_day = (next_month - timedelta(days=1)).day
        midpoint_day = last_day // 2

        return datetime(year, month, midpoint_day)

    elif frequency == "quarterly":
        # Determine quarter
        quarter = (date.month - 1) // 3 + 1

        # Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec
        quarter_start_month = (quarter - 1) * 3 + 1

        # Calculate midpoint (45 days into quarter)
        quarter_start = datetime(date.year, quarter_start_month, 1)
        midpoint = quarter_start + timedelta(days=45)

        return midpoint

    elif frequency == "annual":
        # Midpoint of year (July 2nd or 3rd)
        return datetime(date.year, 7, 2)

    else:
        # Irregular: use date as-is (no adjustment)
        return date
```

---

## Implementation: Get Price with Interpolation

```python
def get_price_on_date(
    self,
    target_date: datetime,
    frequency: str
) -> float:
    """
    Get beta price for a specific date using linear interpolation.

    Args:
        target_date: Date to get price for
        frequency: Frequency of uploaded data

    Returns:
        Interpolated price

    Raises:
        ValueError: If target_date is outside beta data range
    """
    # Convert price dates to midpoints
    midpoints = [(calculate_midpoint(p.date, frequency), p.price)
                 for p in self.prices]

    # Check coverage
    min_date = midpoints[0][0]
    max_date = midpoints[-1][0]

    if target_date < min_date or target_date > max_date:
        raise ValueError(
            f"Beta data does not cover target date {target_date.date()}. "
            f"Beta range: {min_date.date()} to {max_date.date()}. "
            f"Please upload beta prices covering this entire period."
        )

    # Find surrounding points
    for i in range(len(midpoints) - 1):
        date1, price1 = midpoints[i]
        date2, price2 = midpoints[i + 1]

        if date1 <= target_date <= date2:
            # Linear interpolation
            days_total = (date2 - date1).days
            days_from_start = (target_date - date1).days

            if days_total == 0:
                return price1

            weight = days_from_start / days_total
            interpolated_price = price1 + (price2 - price1) * weight

            return interpolated_price

    # Exact match on last point
    if target_date == midpoints[-1][0]:
        return midpoints[-1][1]

    # Should never reach here
    raise ValueError(f"Could not interpolate price for {target_date}")
```

---

## Example Calculations

### Example 1: Monthly Data

**Uploaded CSV:**
```csv
2015-07-01, 100.00
2015-08-01, 105.00
2015-09-01, 103.00
```

**User confirms: "Monthly"**

**Converted to Midpoints:**
```
2015-07-15, 100.00  (mid-July)
2015-08-15, 105.00  (mid-August)
2015-09-15, 103.00  (mid-September)
```

**Get price for 2015-07-25:**
```
Between: 2015-07-15 (100.00) and 2015-08-15 (105.00)
Days from start: 10 days
Days total: 31 days
Weight: 10/31 = 0.3226

Price = 100 + (105 - 100) × 0.3226 = 101.61
```

**Get price for 2015-08-28:**
```
Between: 2015-08-15 (105.00) and 2015-09-15 (103.00)
Days from start: 13 days
Days total: 31 days
Weight: 13/31 = 0.4194

Price = 105 + (103 - 105) × 0.4194 = 104.16
```

### Example 2: Quarterly Data

**Uploaded CSV:**
```csv
2015-01-01, 100.00  (Q1)
2015-04-01, 108.00  (Q2)
2015-07-01, 112.00  (Q3)
```

**User confirms: "Quarterly"**

**Converted to Midpoints:**
```
2015-02-15, 100.00  (mid-Q1: ~45 days into quarter)
2015-05-16, 108.00  (mid-Q2)
2015-08-15, 112.00  (mid-Q3)
```

**Get price for 2015-03-10:**
```
Between: 2015-02-15 (100.00) and 2015-05-16 (108.00)
Days from start: 23 days
Days total: 90 days
Weight: 23/90 = 0.2556

Price = 100 + (108 - 100) × 0.2556 = 102.04
```

---

## Coverage Validation

**Check if beta data covers all investments:**

```python
def validate_beta_coverage(
    investments: List[Investment],
    beta_index: BetaPriceIndex,
    frequency: str
) -> Tuple[bool, List[str]]:
    """
    Validate that beta data covers all investment periods.

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Calculate beta midpoint range
    midpoints = [calculate_midpoint(p.date, frequency) for p in beta_index.prices]
    beta_start = min(midpoints)
    beta_end = max(midpoints)

    # Check each investment
    for inv in investments:
        # Check entry date
        if inv.entry_date < beta_start:
            errors.append(
                f"Investment '{inv.investment_name}' entry date "
                f"({inv.entry_date.date()}) is before beta data start "
                f"({beta_start.date()})"
            )

        # Calculate exit date (we'll estimate using current MOIC/IRR)
        days_held = calculate_holding_period(inv.moic, inv.irr)
        exit_date = inv.entry_date + timedelta(days=days_held)

        if exit_date > beta_end:
            errors.append(
                f"Investment '{inv.investment_name}' estimated exit date "
                f"({exit_date.date()}) is after beta data end "
                f"({beta_end.date()})"
            )

    is_valid = len(errors) == 0
    return is_valid, errors
```

**Display in UI:**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  Beta Data Coverage Issues                              │
│                                                              │
│ The following investments fall outside beta data range:     │
│                                                              │
│ • Alibaba Group: Entry 2011-04-20 before beta start        │
│   (2015-01-01)                                              │
│                                                              │
│ • Future Investment: Exit 2026-12-31 after beta end        │
│   (2025-10-19)                                              │
│                                                              │
│ Please upload beta prices covering:                         │
│   Start: 2011-01-01 or earlier                             │
│   End: 2027-01-01 or later                                 │
│                                                              │
│ Current beta range: 2015-01-01 to 2025-10-19               │
└─────────────────────────────────────────────────────────────┘
```

---

## Questions for Confirmation

### Q1: Midpoint Calculation for Monthly Data

**You said:** "if the user uploads monthly data then assume the price for July is mid july"

**My interpretation:** Price dated 2015-07-01 → represents 2015-07-15

**Is this correct?** Or should we:
- Use the 15th of each month specifically?
- Calculate actual middle day (15th or 16th depending on month length)?

### Q2: What about irregular data?

If user uploads data with inconsistent gaps (e.g., monthly for 2 years, then quarterly):
- Should we still allow it?
- Interpolate each segment separately?
- Require consistent frequency?

### Q3: Edge Case - Exact midpoint match

If investment entry date is exactly 2015-07-15 and we have:
```
2015-07-15, 100.00 (midpoint)
```

Should we:
- Use 100.00 exactly (no interpolation needed)? ✓ I assume yes

### Q4: Year Midpoint

You didn't specify annual midpoint. I assumed July 2nd (day 183 of 365).

**Is this acceptable?** Or different preference?

---

## Summary

**I will implement:**

1. ✅ Frequency detection upon CSV upload
2. ✅ User confirmation dialog with frequency selector
3. ✅ Midpoint calculation based on frequency
4. ✅ Linear interpolation between midpoints
5. ✅ Strict coverage validation
6. ✅ Detailed error messages when coverage insufficient
7. ✅ Show estimated date ranges needed

**This matches your requirements?**

---

**Next Steps:**
1. Confirm midpoint calculation approach
2. Confirm annual/irregular handling
3. Begin implementation

Ready to proceed once confirmed!
