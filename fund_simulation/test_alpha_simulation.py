"""Test script for alpha simulation functionality"""

from datetime import datetime, timedelta
from fund_simulation.models import Investment, BetaPrice, BetaPriceIndex, SimulationConfiguration
from fund_simulation.beta_import import create_beta_index
from fund_simulation.simulation import run_monte_carlo_simulation
from fund_simulation.statistics import calculate_summary_statistics


def create_test_data():
    """Create sample investment and beta data for testing."""
    # Create 5 sample investments
    investments = [
        Investment(
            investment_name="Company A",
            fund_name="Test Fund",
            entry_date=datetime(2020, 1, 1),
            latest_date=datetime(2023, 1, 1),
            moic=2.5,
            irr=0.35
        ),
        Investment(
            investment_name="Company B",
            fund_name="Test Fund",
            entry_date=datetime(2020, 6, 1),
            latest_date=datetime(2023, 6, 1),
            moic=1.8,
            irr=0.22
        ),
        Investment(
            investment_name="Company C",
            fund_name="Test Fund",
            entry_date=datetime(2019, 1, 1),
            latest_date=datetime(2022, 1, 1),
            moic=3.2,
            irr=0.47
        ),
        Investment(
            investment_name="Company D",
            fund_name="Test Fund",
            entry_date=datetime(2021, 1, 1),
            latest_date=datetime(2023, 12, 31),
            moic=1.2,
            irr=0.08
        ),
        Investment(
            investment_name="Company E",
            fund_name="Test Fund",
            entry_date=datetime(2020, 3, 1),
            latest_date=datetime(2023, 3, 1),
            moic=0.8,
            irr=-0.07
        ),
    ]

    # Create beta index (monthly data from 2018-2024)
    beta_prices = []
    current_date = datetime(2018, 1, 1)
    current_price = 100.0

    while current_date <= datetime(2024, 12, 31):
        # Simulate market growth with some volatility
        growth = 1.01  # 1% monthly growth
        beta_prices.append(BetaPrice(date=current_date, price=current_price))
        current_price *= growth

        # Move to next month
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)

    # Create beta index with monthly frequency
    beta_index = create_beta_index(beta_prices, "monthly")

    return investments, beta_index


def test_absolute_simulation():
    """Test absolute return simulation."""
    print("\n" + "="*60)
    print("TEST 1: ABSOLUTE RETURN SIMULATION")
    print("="*60)

    investments, beta_index = create_test_data()

    config = SimulationConfiguration(
        fund_name="Test Fund",
        fund_manager="Test Manager",
        simulation_count=100,
        investment_count_mean=3.0,
        investment_count_std=1.0,
        simulation_type="absolute"
    )

    print(f"Running {config.simulation_count} absolute simulations...")
    results = run_monte_carlo_simulation(investments, config)

    summary = calculate_summary_statistics(results, config)

    print(f"\nResults:")
    print(f"  Mean MOIC: {summary.mean_moic:.2f}x")
    print(f"  Median MOIC: {summary.median_moic:.2f}x")
    print(f"  Mean IRR: {summary.mean_irr:.2%}")
    print(f"  Median IRR: {summary.median_irr:.2%}")

    # Check diagnostic fields
    problematic = sum(1 for r in results if not r.irr_converged)
    neg_cash = sum(1 for r in results if r.has_negative_cash_flows)
    neg_returns = sum(1 for r in results if r.negative_total_returned)

    print(f"\nDiagnostics:")
    print(f"  IRR convergence issues: {problematic}")
    print(f"  Negative cash flows: {neg_cash}")
    print(f"  Negative total returns: {neg_returns}")

    print("\nSUCCESS: Absolute simulation completed successfully")
    return True


def test_alpha_simulation():
    """Test alpha return simulation."""
    print("\n" + "="*60)
    print("TEST 2: ALPHA RETURN SIMULATION")
    print("="*60)

    investments, beta_index = create_test_data()

    config = SimulationConfiguration(
        fund_name="Test Fund",
        fund_manager="Test Manager",
        simulation_count=100,
        investment_count_mean=3.0,
        investment_count_std=1.0,
        simulation_type="alpha"
    )

    print(f"Running {config.simulation_count} alpha simulations...")
    results = run_monte_carlo_simulation(investments, config, beta_index=beta_index)

    summary = calculate_summary_statistics(results, config)

    print(f"\nResults:")
    print(f"  Mean MOIC: {summary.mean_moic:.2f}x")
    print(f"  Median MOIC: {summary.median_moic:.2f}x")
    print(f"  Mean IRR: {summary.mean_irr:.2%}")
    print(f"  Median IRR: {summary.median_irr:.2%}")

    # Check diagnostic fields
    problematic = sum(1 for r in results if not r.irr_converged)
    neg_cash = sum(1 for r in results if r.has_negative_cash_flows)
    neg_returns = sum(1 for r in results if r.negative_total_returned)

    print(f"\nDiagnostics:")
    print(f"  IRR convergence issues: {problematic}")
    print(f"  Negative cash flows: {neg_cash}")
    print(f"  Negative total returns: {neg_returns}")

    print("\nSUCCESS: Alpha simulation completed successfully")
    return True


def test_beta_interpolation():
    """Test beta price interpolation."""
    print("\n" + "="*60)
    print("TEST 3: BETA PRICE INTERPOLATION")
    print("="*60)

    _, beta_index = create_test_data()

    # Test getting price for a date between data points
    test_date = datetime(2020, 7, 15)
    price = beta_index.get_price_on_date(test_date)
    print(f"\nPrice on {test_date.date()}: {price:.2f}")

    # Test calculating return over period
    entry = datetime(2020, 1, 1)
    exit_date = datetime(2023, 1, 1)
    beta_moic, beta_irr = beta_index.calculate_return(entry, exit_date)

    print(f"\nBeta return from {entry.date()} to {exit_date.date()}:")
    print(f"  Beta MOIC: {beta_moic:.2f}x")
    print(f"  Beta IRR: {beta_irr:.2%}")

    print("\nSUCCESS: Beta interpolation working correctly")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ALPHA SIMULATION FUNCTIONALITY TESTS")
    print("="*60)

    tests_passed = 0
    tests_failed = 0

    try:
        if test_beta_interpolation():
            tests_passed += 1
    except Exception as e:
        print(f"\nERROR in beta interpolation test: {str(e)}")
        tests_failed += 1

    try:
        if test_absolute_simulation():
            tests_passed += 1
    except Exception as e:
        print(f"\nERROR in absolute simulation test: {str(e)}")
        tests_failed += 1

    try:
        if test_alpha_simulation():
            tests_passed += 1
    except Exception as e:
        print(f"\nERROR in alpha simulation test: {str(e)}")
        tests_failed += 1

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {tests_passed}/3")
    print(f"Tests failed: {tests_failed}/3")

    if tests_failed == 0:
        print("\nALL TESTS PASSED")
        return 0
    else:
        print("\nSOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
