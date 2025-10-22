# Monte Carlo Fund Simulation - Test Specifications

**Version:** 1.0
**Last Updated:** 2025-10-19

---

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Unit Tests](#unit-tests)
3. [Integration Tests](#integration-tests)
4. [End-to-End Tests](#end-to-end-tests)
5. [Edge Case Tests](#edge-case-tests)
6. [Performance Tests](#performance-tests)
7. [Expected Results & Validation](#expected-results--validation)

---

## Testing Strategy

### Test Pyramid

```
        ┌────────────────┐
        │  E2E Tests     │  (Few, slow, comprehensive)
        │  ~ 5 tests     │
        ├────────────────┤
        │ Integration    │  (Some, medium speed)
        │ Tests          │
        │ ~ 15 tests     │
        ├────────────────┤
        │  Unit Tests    │  (Many, fast, focused)
        │  ~ 50 tests    │
        └────────────────┘
```

### Test Categories

1. **Unit Tests** - Test individual functions in isolation
2. **Integration Tests** - Test component interactions
3. **End-to-End Tests** - Test complete workflows
4. **Edge Case Tests** - Test boundary conditions
5. **Performance Tests** - Verify speed requirements

### Testing Tools

```python
# Core testing
import pytest
import numpy as np
from datetime import datetime

# Assertion helpers
from numpy.testing import assert_almost_equal
```

---

## Unit Tests

### Test Suite 1: Data Models

#### Test 1.1: Investment Validation - Valid Investment

```python
def test_investment_valid():
    """Test that a valid investment passes validation."""
    inv = Investment(
        investment_name="Alibaba Group",
        fund_name="Fund I",
        entry_date=datetime(2011, 4, 20),
        latest_date=datetime(2015, 3, 23),
        moic=12.38,
        irr=0.8983
    )

    errors = inv.validate()

    assert len(errors) == 0, f"Expected no errors, got: {errors}"
    assert inv.days_held > 0
```

**Expected Result:**
- No validation errors
- days_held = 1433 days

#### Test 1.2: Investment Validation - Empty Name

```python
def test_investment_empty_name():
    """Test that empty investment name fails validation."""
    inv = Investment(
        investment_name="",
        fund_name="Fund I",
        entry_date=datetime(2011, 4, 20),
        latest_date=datetime(2015, 3, 23),
        moic=12.38,
        irr=0.8983
    )

    errors = inv.validate()

    assert len(errors) > 0
    assert any("name is required" in err.lower() for err in errors)
```

**Expected Result:**
- 1 error: "Investment name is required"

#### Test 1.3: Investment Validation - Invalid Date Order

```python
def test_investment_invalid_dates():
    """Test that entry_date >= latest_date fails validation."""
    inv = Investment(
        investment_name="Test Co",
        fund_name="Fund I",
        entry_date=datetime(2023, 1, 1),
        latest_date=datetime(2020, 1, 1),
        moic=2.0,
        irr=0.25
    )

    errors = inv.validate()

    assert len(errors) > 0
    assert any("before" in err.lower() for err in errors)
```

**Expected Result:**
- 1 error containing "before"

#### Test 1.4: Investment Validation - Negative MOIC

```python
def test_investment_negative_moic():
    """Test that negative MOIC fails validation."""
    inv = Investment(
        investment_name="Test Co",
        fund_name="Fund I",
        entry_date=datetime(2020, 1, 1),
        latest_date=datetime(2023, 1, 1),
        moic=-0.5,
        irr=0.25
    )

    errors = inv.validate()

    assert len(errors) > 0
    assert any("negative" in err.lower() for err in errors)
```

**Expected Result:**
- 1 error about negative MOIC

#### Test 1.5: Investment Validation - IRR < -100%

```python
def test_investment_invalid_irr():
    """Test that IRR < -1.0 fails validation."""
    inv = Investment(
        investment_name="Test Co",
        fund_name="Fund I",
        entry_date=datetime(2020, 1, 1),
        latest_date=datetime(2023, 1, 1),
        moic=0.5,
        irr=-1.5  # -150%, impossible
    )

    errors = inv.validate()

    assert len(errors) > 0
    assert any("-100%" in err for err in errors)
```

**Expected Result:**
- 1 error: "IRR cannot be less than -100%"

#### Test 1.6: Configuration Validation - Valid Config

```python
def test_config_valid():
    """Test that valid configuration passes validation."""
    config = SimulationConfiguration(
        fund_name="Test Fund",
        fund_manager="Test Manager",
        leverage_rate=0.5,
        cost_of_capital=0.08,
        fee_rate=0.02,
        carry_rate=0.20,
        hurdle_rate=0.08,
        simulation_count=10000,
        investment_count_mean=10.0,
        investment_count_std=2.0
    )

    errors = config.validate()

    assert len(errors) == 0, f"Expected no errors, got: {errors}"
```

**Expected Result:**
- No validation errors

#### Test 1.7: Configuration Validation - Invalid Ranges

```python
def test_config_invalid_ranges():
    """Test that out-of-range parameters fail validation."""
    config = SimulationConfiguration(
        fund_name="Test Fund",
        fund_manager="Test Manager",
        leverage_rate=1.5,  # > 100%
        fee_rate=0.15,      # > 10%
        carry_rate=0.6,     # > 50%
        simulation_count=50  # < 100
    )

    errors = config.validate()

    assert len(errors) >= 4
    assert any("leverage" in err.lower() for err in errors)
    assert any("fee" in err.lower() for err in errors)
    assert any("carry" in err.lower() for err in errors)
    assert any("simulation count" in err.lower() for err in errors)
```

**Expected Result:**
- 4 errors for out-of-range parameters

---

### Test Suite 2: Core Calculators

#### Test 2.1: Holding Period - Normal Case

```python
def test_holding_period_normal():
    """Test holding period calculation with normal values."""
    from fund_simulation.calculators import calculate_holding_period

    # MOIC = 2.0, IRR = 25% → Expected ~1134 days
    days = calculate_holding_period(moic=2.0, irr=0.25)

    assert 1100 <= days <= 1200, f"Expected ~1134 days, got {days}"
```

**Expected Result:**
- days ≈ 1134 (within 1100-1200 range)

**Formula Check:**
```
days = 365 × ln(2.0) / ln(1.25)
     = 365 × 0.6931 / 0.2231
     = 365 × 3.1063
     = 1133.8 ≈ 1134
```

#### Test 2.2: Holding Period - Edge Case MOIC = 0

```python
def test_holding_period_zero_moic():
    """Test holding period when MOIC = 0 (total loss)."""
    from fund_simulation.calculators import calculate_holding_period

    days = calculate_holding_period(moic=0, irr=0.25)

    assert days == 365, f"Expected 365 days (default), got {days}"
```

**Expected Result:**
- days = 365 (default fallback)

#### Test 2.3: Holding Period - Edge Case IRR = -1.0

```python
def test_holding_period_irr_negative_one():
    """Test holding period when IRR = -1.0 (-100%)."""
    from fund_simulation.calculators import calculate_holding_period

    days = calculate_holding_period(moic=0.5, irr=-1.0)

    # Should adjust IRR to -0.9999 internally
    assert days >= 1, f"Expected at least 1 day, got {days}"
```

**Expected Result:**
- days ≥ 1 (calculation succeeds with adjusted IRR)

#### Test 2.4: IRR Calculation - Simple Case

```python
def test_irr_simple():
    """Test IRR calculation with simple cash flows."""
    from fund_simulation.calculators import calculate_irr

    # $1M invested, $1.5M returned after 2 years (730 days)
    cash_flows = {730: 1_500_000}
    irr = calculate_irr(cash_flows, 1_000_000)

    # Expected IRR ≈ 22.47%
    assert 0.20 <= irr <= 0.25, f"Expected IRR ~0.2247, got {irr:.4f}"
```

**Expected Result:**
- IRR ≈ 0.2247 (22.47%)

**Manual Verification:**
```
NPV = -1,000,000 + 1,500,000 / (1 + r)^2 = 0
1,500,000 / (1 + r)^2 = 1,000,000
(1 + r)^2 = 1.5
1 + r = 1.2247
r = 0.2247 (22.47%)
```

#### Test 2.5: IRR Calculation - Multiple Cash Flows

```python
def test_irr_multiple_cash_flows():
    """Test IRR with multiple cash flows on different days."""
    from fund_simulation.calculators import calculate_irr

    # $2M invested
    # $500K returned after 1 year, $2M returned after 3 years
    cash_flows = {
        365: 500_000,
        1095: 2_000_000
    }
    irr = calculate_irr(cash_flows, 2_000_000)

    # Should converge to positive IRR
    assert irr > 0, f"Expected positive IRR, got {irr:.4f}"
    assert irr < 1.0, f"Expected reasonable IRR < 100%, got {irr:.4f}"
```

**Expected Result:**
- IRR > 0 and < 1.0
- Converges within 100 iterations

#### Test 2.6: MOIC Calculation

```python
def test_moic_calculation():
    """Test MOIC calculation."""
    from fund_simulation.calculators import calculate_moic

    # $1M invested, $2.5M returned
    moic = calculate_moic(2_500_000, 1_000_000)

    assert abs(moic - 2.5) < 0.001, f"Expected 2.5, got {moic}"
```

**Expected Result:**
- MOIC = 2.5

#### Test 2.7: MOIC Calculation - Zero Investment

```python
def test_moic_zero_investment():
    """Test MOIC when investment is zero (edge case)."""
    from fund_simulation.calculators import calculate_moic

    moic = calculate_moic(1_000_000, 0)

    assert moic == 0.0, f"Expected 0.0, got {moic}"
```

**Expected Result:**
- MOIC = 0.0 (avoids division by zero)

---

### Test Suite 3: Data Import

#### Test 3.1: CSV Parsing - Valid File

```python
def test_csv_parsing_valid():
    """Test parsing a valid CSV file."""
    from fund_simulation.data_import import parse_csv_file

    # Create test CSV
    csv_content = """Alibaba Group,Fund I,2011-04-20,2015-03-23,12.38,0.8983
Bazaarvoice,Fund I,2011-07-20,2012-09-10,0.88,-0.0381
DrillingInfo,Fund I,2012-02-29,2018-08-01,3.44,0.2138"""

    with open('test_valid.csv', 'w') as f:
        f.write(csv_content)

    investments, errors = parse_csv_file('test_valid.csv')

    assert len(investments) == 3, f"Expected 3 investments, got {len(investments)}"
    assert len(errors) == 0, f"Expected no errors, got {errors}"

    # Check first investment
    inv = investments[0]
    assert inv.investment_name == "Alibaba Group"
    assert inv.fund_name == "Fund I"
    assert abs(inv.moic - 12.38) < 0.01
    assert abs(inv.irr - 0.8983) < 0.001
```

**Expected Result:**
- 3 investments loaded
- No errors
- First investment matches expected values

#### Test 3.2: CSV Parsing - Wrong Column Count

```python
def test_csv_wrong_column_count():
    """Test that rows with wrong column count are rejected."""
    from fund_simulation.data_import import parse_csv_file

    csv_content = """Alibaba Group,Fund I,2011-04-20,2015-03-23,12.38
Bazaarvoice,Fund I,2011-07-20,2012-09-10,0.88,-0.0381"""  # First row only 5 cols

    with open('test_wrong_cols.csv', 'w') as f:
        f.write(csv_content)

    investments, errors = parse_csv_file('test_wrong_cols.csv')

    assert len(investments) == 1, "Only second row should be parsed"
    assert len(errors) >= 1, "Should have at least one error"
    assert any("6 columns" in err.lower() for err in errors)
```

**Expected Result:**
- 1 investment (second row only)
- 1+ errors about column count

#### Test 3.3: CSV Parsing - Invalid Date Format

```python
def test_csv_invalid_date():
    """Test that invalid dates are caught."""
    from fund_simulation.data_import import parse_csv_file

    csv_content = """Test Co,Fund I,INVALID_DATE,2015-03-23,2.0,0.25"""

    with open('test_invalid_date.csv', 'w') as f:
        f.write(csv_content)

    investments, errors = parse_csv_file('test_invalid_date.csv')

    assert len(investments) == 0
    assert len(errors) >= 1
    assert any("date" in err.lower() for err in errors)
```

**Expected Result:**
- 0 investments
- 1+ errors about invalid date

#### Test 3.4: CSV Parsing - IRR Adjustment

```python
def test_csv_irr_adjustment():
    """Test that IRR = -1.0 is adjusted to -0.9999."""
    from fund_simulation.data_import import parse_csv_file

    csv_content = """Total Loss,Fund I,2011-04-20,2015-03-23,0.0,-1.0"""

    with open('test_irr_adjust.csv', 'w') as f:
        f.write(csv_content)

    investments, errors = parse_csv_file('test_irr_adjust.csv')

    assert len(investments) == 1
    assert investments[0].irr == -0.9999, f"Expected -0.9999, got {investments[0].irr}"
```

**Expected Result:**
- 1 investment
- IRR = -0.9999 (adjusted from -1.0)

---

### Test Suite 4: Simulation Engine

#### Test 4.1: Portfolio Size Generation

```python
def test_portfolio_size_generation():
    """Test portfolio size generation from normal distribution."""
    from fund_simulation.simulation import generate_portfolio_size
    import numpy as np

    random_state = np.random.RandomState(seed=42)

    sizes = [
        generate_portfolio_size(10.0, 2.0, 50, random_state)
        for _ in range(1000)
    ]

    # Check that sizes are within bounds
    assert all(1 <= size <= 100 for size in sizes), "Sizes out of bounds"

    # Check mean is approximately correct
    mean_size = np.mean(sizes)
    assert 9.0 <= mean_size <= 11.0, f"Mean should be ~10, got {mean_size}"
```

**Expected Result:**
- All sizes in range [1, 100]
- Mean ≈ 10

#### Test 4.2: Investment Selection WITH Replacement

```python
def test_investment_selection():
    """Test that investment selection allows duplicates (WITH REPLACEMENT)."""
    from fund_simulation.simulation import select_investments
    from fund_simulation.models import Investment
    from datetime import datetime
    import numpy as np

    # Create 3 investments
    investments = [
        Investment("A", "Fund", datetime(2020,1,1), datetime(2023,1,1), 2.0, 0.25),
        Investment("B", "Fund", datetime(2020,1,1), datetime(2023,1,1), 2.0, 0.25),
        Investment("C", "Fund", datetime(2020,1,1), datetime(2023,1,1), 2.0, 0.25),
    ]

    random_state = np.random.RandomState(seed=42)

    # Select 100 investments (much more than available)
    selected = select_investments(investments, 100, random_state)

    assert len(selected) == 100, f"Expected 100 selections, got {len(selected)}"

    # Check that duplicates exist (with high probability)
    selected_names = [inv.investment_name for inv in selected]
    unique_names = set(selected_names)
    assert len(unique_names) < 100, "Should have duplicates with replacement"
```

**Expected Result:**
- 100 selections made
- Duplicates present (fewer than 100 unique names)

#### Test 4.3: Single Simulation - Basic Execution

```python
def test_single_simulation():
    """Test that a single simulation executes without errors."""
    from fund_simulation.simulation import run_single_simulation
    from fund_simulation.models import Investment, SimulationConfiguration
    from datetime import datetime
    import numpy as np

    investments = [
        Investment("Test 1", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 2.5, 0.35),
        Investment("Test 2", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 1.8, 0.22),
        Investment("Test 3", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 3.0, 0.45),
    ]

    config = SimulationConfiguration(
        fund_name="Test",
        fund_manager="Test Manager",
        simulation_count=1
    )

    random_state = np.random.RandomState(seed=42)

    result = run_single_simulation(investments, config, 0, random_state)

    assert result.simulation_id == 0
    assert result.investment_count > 0
    assert result.total_invested > 0
    assert result.moic > 0
```

**Expected Result:**
- SimulationResult object created
- All fields populated with reasonable values

#### Test 4.4: Full Monte Carlo Simulation

```python
def test_monte_carlo_simulation():
    """Test complete Monte Carlo simulation."""
    from fund_simulation.simulation import run_monte_carlo_simulation
    from fund_simulation.models import Investment, SimulationConfiguration
    from datetime import datetime

    investments = [
        Investment("Test 1", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 2.5, 0.35),
        Investment("Test 2", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 1.8, 0.22),
        Investment("Test 3", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 3.0, 0.45),
    ]

    config = SimulationConfiguration(
        fund_name="Test",
        fund_manager="Test Manager",
        simulation_count=1000
    )

    results = run_monte_carlo_simulation(investments, config)

    assert len(results) == 1000, f"Expected 1000 results, got {len(results)}"
    assert all(r.moic > 0 for r in results), "All MOICs should be positive"
```

**Expected Result:**
- 1000 simulation results
- All results have reasonable values

---

### Test Suite 5: Financial Engineering

#### Test 5.1: Leverage Calculation

```python
def test_leverage_calculation():
    """Test leverage amplification."""
    # Manual calculation
    total_invested = 10_000_000
    leverage_rate = 0.5  # 50%
    leverage_amount = total_invested * leverage_rate
    total_capital = total_invested + leverage_amount

    assert leverage_amount == 5_000_000
    assert total_capital == 15_000_000
```

**Expected Result:**
- Leverage Amount = $5M
- Total Capital = $15M

#### Test 5.2: Management Fees Calculation

```python
def test_management_fees():
    """Test time-weighted management fees."""
    total_capital = 15_000_000
    fee_rate = 0.02  # 2% per year
    years_held = 3.5

    management_fees = total_capital * fee_rate * years_held

    expected = 15_000_000 * 0.02 * 3.5
    assert abs(management_fees - expected) < 0.01
    assert abs(management_fees - 1_050_000) < 0.01
```

**Expected Result:**
- Management Fees = $1,050,000

#### Test 5.3: Carry Calculation - Above Hurdle

```python
def test_carry_above_hurdle():
    """Test carry when returns exceed hurdle."""
    total_capital = 15_000_000
    hurdle_rate = 0.08
    years_held = 3.5
    carry_rate = 0.20

    total_returned = 20_000_000

    hurdle_return = total_capital * (1 + hurdle_rate * years_held)
    excess_return = max(0, total_returned - hurdle_return)
    carry_paid = excess_return * carry_rate

    expected_hurdle = 15_000_000 * (1 + 0.08 * 3.5)  # = 19,200,000
    expected_excess = 20_000_000 - 19_200_000  # = 800,000
    expected_carry = 800_000 * 0.20  # = 160,000

    assert abs(hurdle_return - expected_hurdle) < 0.01
    assert abs(excess_return - expected_excess) < 0.01
    assert abs(carry_paid - expected_carry) < 0.01
```

**Expected Result:**
- Hurdle Return = $19,200,000
- Excess Return = $800,000
- Carry Paid = $160,000

#### Test 5.4: Carry Calculation - Below Hurdle

```python
def test_carry_below_hurdle():
    """Test that no carry is paid when below hurdle."""
    total_capital = 15_000_000
    hurdle_rate = 0.08
    years_held = 3.5
    carry_rate = 0.20

    total_returned = 18_000_000  # Below hurdle

    hurdle_return = total_capital * (1 + hurdle_rate * years_held)
    excess_return = max(0, total_returned - hurdle_return)
    carry_paid = excess_return * carry_rate

    assert excess_return == 0, "No excess return"
    assert carry_paid == 0, "No carry paid"
```

**Expected Result:**
- Excess Return = $0
- Carry Paid = $0

---

## Integration Tests

### Test 6.1: End-to-End Workflow

```python
def test_end_to_end_workflow():
    """Test complete workflow from CSV to results."""
    from fund_simulation.data_import import parse_csv_file
    from fund_simulation.models import SimulationConfiguration
    from fund_simulation.simulation import run_monte_carlo_simulation
    from fund_simulation.statistics import calculate_summary_statistics

    # 1. Create test CSV
    csv_content = """Alibaba Group,Fund I,2011-04-20,2015-03-23,12.38,0.8983
Bazaarvoice,Fund I,2011-07-20,2012-09-10,0.88,-0.0381
DrillingInfo,Fund I,2012-02-29,2018-08-01,3.44,0.2138
Marketo,Fund I,2011-11-15,2013-11-21,2.33,0.5222"""

    with open('test_e2e.csv', 'w') as f:
        f.write(csv_content)

    # 2. Parse CSV
    investments, errors = parse_csv_file('test_e2e.csv')
    assert len(errors) == 0
    assert len(investments) == 4

    # 3. Create config
    config = SimulationConfiguration(
        fund_name="Test Fund",
        fund_manager="Test Manager",
        simulation_count=1000
    )
    errors = config.validate()
    assert len(errors) == 0

    # 4. Generate hashes
    data_hash, total_hash = config.generate_hash(investments)
    assert len(data_hash) == 64  # SHA256 hex
    assert len(total_hash) == 64

    # 5. Run simulation
    results = run_monte_carlo_simulation(investments, config)
    assert len(results) == 1000

    # 6. Calculate statistics
    summary = calculate_summary_statistics(results, config)
    assert summary.total_runs == 1000
    assert summary.mean_moic > 0
    assert summary.median_moic > 0
    assert -1.0 <= summary.mean_irr <= 10.0

    print(f"✓ E2E Test Passed")
    print(f"  Mean MOIC: {summary.mean_moic:.2f}x")
    print(f"  Median MOIC: {summary.median_moic:.2f}x")
    print(f"  Mean IRR: {summary.mean_irr:.2%}")
    print(f"  Median IRR: {summary.median_irr:.2%}")
```

**Expected Result:**
- All steps execute successfully
- Summary statistics within reasonable ranges

---

## Edge Case Tests

### Test 7.1: All Investments Are Losses

```python
def test_all_losses():
    """Test simulation when all investments are losses."""
    from fund_simulation.simulation import run_single_simulation
    from fund_simulation.models import Investment, SimulationConfiguration
    from datetime import datetime
    import numpy as np

    # All investments lost money
    investments = [
        Investment("Loss 1", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 0.5, -0.20),
        Investment("Loss 2", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 0.3, -0.35),
        Investment("Loss 3", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 0.1, -0.60),
    ]

    config = SimulationConfiguration(
        fund_name="Test",
        fund_manager="Test Manager"
    )

    random_state = np.random.RandomState(seed=42)
    result = run_single_simulation(investments, config, 0, random_state)

    assert result.moic < 1.0, "MOIC should be less than 1.0 (loss)"
    assert result.irr < 0, "IRR should be negative"
```

**Expected Result:**
- MOIC < 1.0
- IRR < 0
- No errors during execution

### Test 7.2: Single Investment Universe

```python
def test_single_investment():
    """Test simulation with only one investment in universe."""
    from fund_simulation.simulation import run_single_simulation
    from fund_simulation.models import Investment, SimulationConfiguration
    from datetime import datetime
    import numpy as np

    investments = [
        Investment("Only One", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 2.5, 0.35)
    ]

    config = SimulationConfiguration(
        fund_name="Test",
        fund_manager="Test Manager",
        investment_count_mean=5.0  # Will select same investment multiple times
    )

    random_state = np.random.RandomState(seed=42)
    result = run_single_simulation(investments, config, 0, random_state)

    # All selections should be the same investment
    assert result.investment_count >= 1
    assert all(name == "Only One" for name in result.investments_selected)
```

**Expected Result:**
- Simulation executes
- All selected investments are "Only One"

### Test 7.3: Extreme Leverage (100%)

```python
def test_extreme_leverage():
    """Test simulation with 100% leverage."""
    from fund_simulation.simulation import run_single_simulation
    from fund_simulation.models import Investment, SimulationConfiguration
    from datetime import datetime
    import numpy as np

    investments = [
        Investment("Test", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 2.0, 0.25)
    ]

    config = SimulationConfiguration(
        fund_name="Test",
        fund_manager="Test Manager",
        leverage_rate=1.0,  # 100% leverage
        cost_of_capital=0.10
    )

    random_state = np.random.RandomState(seed=42)
    result = run_single_simulation(investments, config, 0, random_state)

    # Leverage cost should be significant
    assert result.leverage_cost > 0
    assert result.moic != result.gross_profit / result.total_invested
```

**Expected Result:**
- High leverage cost
- Net MOIC significantly reduced by leverage cost

---

## Performance Tests

### Test 8.1: 1,000 Simulations Performance

```python
def test_performance_1000():
    """Test that 1,000 simulations complete in < 10 seconds."""
    import time
    from fund_simulation.simulation import run_monte_carlo_simulation
    from fund_simulation.models import Investment, SimulationConfiguration
    from datetime import datetime

    investments = [
        Investment(f"Test {i}", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 2.0, 0.25)
        for i in range(20)
    ]

    config = SimulationConfiguration(
        fund_name="Test",
        fund_manager="Test Manager",
        simulation_count=1000
    )

    start_time = time.time()
    results = run_monte_carlo_simulation(investments, config)
    elapsed = time.time() - start_time

    assert len(results) == 1000
    assert elapsed < 10.0, f"Expected < 10s, took {elapsed:.2f}s"
    print(f"  1,000 simulations: {elapsed:.2f}s")
```

**Expected Result:**
- Completes in < 10 seconds
- Target: < 5 seconds

### Test 8.2: 10,000 Simulations Performance

```python
def test_performance_10000():
    """Test that 10,000 simulations complete in < 120 seconds."""
    import time
    from fund_simulation.simulation import run_monte_carlo_simulation
    from fund_simulation.models import Investment, SimulationConfiguration
    from datetime import datetime

    investments = [
        Investment(f"Test {i}", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 2.0, 0.25)
        for i in range(20)
    ]

    config = SimulationConfiguration(
        fund_name="Test",
        fund_manager="Test Manager",
        simulation_count=10000
    )

    start_time = time.time()
    results = run_monte_carlo_simulation(investments, config)
    elapsed = time.time() - start_time

    assert len(results) == 10000
    assert elapsed < 120.0, f"Expected < 120s, took {elapsed:.2f}s"
    print(f"  10,000 simulations: {elapsed:.2f}s")
```

**Expected Result:**
- Completes in < 120 seconds
- Target: < 60 seconds

---

## Expected Results & Validation

### Validation Test 1: Reproducibility

```python
def test_reproducibility():
    """Test that same inputs produce identical results."""
    from fund_simulation.simulation import run_monte_carlo_simulation
    from fund_simulation.models import Investment, SimulationConfiguration
    from datetime import datetime

    investments = [
        Investment("Test 1", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 2.5, 0.35),
        Investment("Test 2", "Fund I", datetime(2020,1,1), datetime(2023,1,1), 1.8, 0.22),
    ]

    config = SimulationConfiguration(
        fund_name="Test",
        fund_manager="Test Manager",
        simulation_count=100
    )

    # Run simulation twice
    results1 = run_monte_carlo_simulation(investments, config)
    results2 = run_monte_carlo_simulation(investments, config)

    # Results should be identical (due to seed=42)
    for i in range(100):
        assert results1[i].moic == results2[i].moic
        assert results1[i].irr == results2[i].irr
        assert results1[i].investment_count == results2[i].investment_count

    print("✓ Reproducibility verified (seed=42 works)")
```

**Expected Result:**
- Both runs produce identical results
- Same MOIC, IRR, and investment selections

### Validation Test 2: Real Data Test

Using the actual Lead Edge Deals.csv file:

```python
def test_real_data():
    """Test with actual Lead Edge investment data."""
    from fund_simulation.data_import import parse_csv_file
    from fund_simulation.models import SimulationConfiguration
    from fund_simulation.simulation import run_monte_carlo_simulation
    from fund_simulation.statistics import calculate_summary_statistics

    # Parse real data
    investments, errors = parse_csv_file('../Lead Edge Deals.csv')

    print(f"Loaded {len(investments)} real investments")
    assert len(investments) > 50, "Should have many investments"

    # Run simulation with realistic params
    config = SimulationConfiguration(
        fund_name="Simulated Lead Edge Fund",
        fund_manager="Lead Edge Capital",
        leverage_rate=0.0,  # No leverage
        cost_of_capital=0.08,
        fee_rate=0.02,
        carry_rate=0.20,
        hurdle_rate=0.08,
        simulation_count=10000,
        investment_count_mean=15.0,
        investment_count_std=3.0
    )

    results = run_monte_carlo_simulation(investments, config)
    summary = calculate_summary_statistics(results, config)

    print("\n=== Real Data Simulation Results ===")
    print(f"Mean MOIC: {summary.mean_moic:.2f}x")
    print(f"Median MOIC: {summary.median_moic:.2f}x")
    print(f"5th Percentile MOIC: {summary.percentile_5_moic:.2f}x")
    print(f"95th Percentile MOIC: {summary.percentile_95_moic:.2f}x")
    print(f"\nMean IRR: {summary.mean_irr:.2%}")
    print(f"Median IRR: {summary.median_irr:.2%}")
    print(f"5th Percentile IRR: {summary.percentile_5_irr:.2%}")
    print(f"95th Percentile IRR: {summary.percentile_95_irr:.2%}")

    # Sanity checks
    assert summary.mean_moic > 0.5, "Mean MOIC should be reasonable"
    assert summary.mean_moic < 10.0, "Mean MOIC shouldn't be extreme"
    assert -0.5 <= summary.mean_irr <= 2.0, "Mean IRR should be reasonable"
```

**Expected Result:**
- Successfully loads 107 investments
- Mean MOIC in reasonable range (likely 1.5x - 3.0x)
- Mean IRR in reasonable range (likely 15% - 40%)
- No errors during execution

---

## Test Execution Plan

### Phase 1: Unit Tests

```bash
pytest tests/test_models.py -v
pytest tests/test_calculators.py -v
pytest tests/test_data_import.py -v
```

### Phase 2: Integration Tests

```bash
pytest tests/test_simulation.py -v
pytest tests/test_statistics.py -v
```

### Phase 3: End-to-End Tests

```bash
pytest tests/test_integration.py -v
```

### Phase 4: Performance Tests

```bash
pytest tests/test_performance.py -v --durations=10
```

### Phase 5: Real Data Validation

```bash
python tests/test_real_data.py
```

---

## Success Criteria

### All Tests Must Pass

- [ ] 100% of unit tests pass
- [ ] 100% of integration tests pass
- [ ] 100% of edge case tests pass
- [ ] Performance tests meet targets
- [ ] Real data test produces reasonable results

### Code Coverage

- [ ] Core calculators: 100% coverage
- [ ] Data models: 100% coverage
- [ ] Simulation engine: 95%+ coverage
- [ ] Data import: 95%+ coverage

### Manual Validation Checklist

- [ ] CSV import handles all edge cases
- [ ] Configuration validation catches all errors
- [ ] Simulation produces reproducible results
- [ ] Financial engineering calculations are correct
- [ ] Statistical summary is accurate
- [ ] Performance meets targets
- [ ] UI displays results correctly

---

**End of Test Specifications**
