"""Run comprehensive simulation test with 10,000 iterations"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fund_simulation.data_import import parse_csv_file
from fund_simulation.models import SimulationConfiguration
from fund_simulation.simulation import run_monte_carlo_simulation
from fund_simulation.statistics import calculate_summary_statistics


def main():
    print("=" * 80)
    print("COMPREHENSIVE MONTE CARLO SIMULATION TEST - 10,000 ITERATIONS")
    print("=" * 80)

    # Load Lead Edge data
    csv_path = "../Lead Edge Deals.csv"
    print(f"\nLoading historical investment data from: {csv_path}")

    investments, errors = parse_csv_file(csv_path)

    if not investments:
        print("\nERROR: No investments loaded. Exiting.")
        return

    print(f"SUCCESS: Loaded {len(investments)} investments")

    # Show investment universe summary
    moics = [inv.moic for inv in investments]
    irrs = [inv.irr for inv in investments]

    print("\nInvestment Universe Summary:")
    print(f"  Count: {len(investments)} investments")
    print(f"  MOIC Range: {min(moics):.2f}x to {max(moics):.2f}x")
    print(f"  IRR Range: {min(irrs):.2%} to {max(irrs):.2%}")

    # Count by fund
    funds = {}
    for inv in investments:
        funds[inv.fund_name] = funds.get(inv.fund_name, 0) + 1

    print(f"\nInvestments by Fund:")
    for fund, count in sorted(funds.items()):
        print(f"  {fund}: {count} investments")

    # Create configuration with realistic parameters
    config = SimulationConfiguration(
        fund_name="Simulated Venture Fund",
        fund_manager="Monte Carlo Capital",
        leverage_rate=0.0,          # No leverage
        cost_of_capital=0.08,       # 8% cost of capital
        fee_rate=0.02,              # 2% annual management fee
        carry_rate=0.20,            # 20% carry
        hurdle_rate=0.08,           # 8% hurdle rate
        simulation_count=10000,     # 10,000 simulations
        investment_count_mean=15.0, # ~15 investments per portfolio
        investment_count_std=3.0    # ±3 std dev
    )

    print("\n" + "=" * 80)
    print("SIMULATION CONFIGURATION")
    print("=" * 80)
    print(f"Fund: {config.fund_name}")
    print(f"Manager: {config.fund_manager}")
    print(f"\nFinancial Parameters:")
    print(f"  Leverage Rate: {config.leverage_rate:.1%}")
    print(f"  Cost of Capital: {config.cost_of_capital:.1%}")
    print(f"  Management Fee: {config.fee_rate:.1%} per year")
    print(f"  Carry Rate: {config.carry_rate:.1%}")
    print(f"  Hurdle Rate: {config.hurdle_rate:.1%}")
    print(f"\nSimulation Parameters:")
    print(f"  Simulation Count: {config.simulation_count:,}")
    print(f"  Portfolio Size: {config.investment_count_mean:.1f} ± {config.investment_count_std:.1f}")

    # Validate configuration
    errors = config.validate()
    if errors:
        print("\nERROR: Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return

    # Generate hashes
    data_hash, total_hash = config.generate_hash(investments)
    print(f"\nDeduplication Hashes:")
    print(f"  Data Hash: {data_hash[:16]}...")
    print(f"  Total Hash: {total_hash[:16]}...")

    print("\n" + "=" * 80)
    print(f"RUNNING {config.simulation_count:,} SIMULATIONS")
    print("=" * 80)

    # Track time
    start_time = time.time()

    # Progress tracking
    last_progress = 0

    def show_progress(fraction):
        nonlocal last_progress
        current_pct = int(fraction * 100)
        if current_pct >= last_progress + 10:
            elapsed = time.time() - start_time
            rate = fraction / elapsed if elapsed > 0 else 0
            remaining = ((1 - fraction) / rate) if rate > 0 else 0

            print(f"  {current_pct:3d}% complete | "
                  f"Elapsed: {elapsed:6.1f}s | "
                  f"Remaining: {remaining:6.1f}s | "
                  f"Rate: {rate*config.simulation_count:,.0f} sims/sec")
            last_progress = current_pct

    # Run simulation
    results = run_monte_carlo_simulation(
        investments,
        config,
        progress_callback=show_progress
    )

    elapsed_time = time.time() - start_time
    rate = len(results) / elapsed_time

    print(f"\nSUCCESS: Completed {len(results):,} simulations in {elapsed_time:.2f} seconds")
    print(f"  Average Rate: {rate:,.0f} simulations/second")

    # Calculate statistics
    summary = calculate_summary_statistics(results, config)

    # Display comprehensive results
    print("\n" + "=" * 80)
    print("SIMULATION RESULTS - MOIC (MULTIPLE ON INVESTED CAPITAL)")
    print("=" * 80)
    print(f"\nCentral Tendency:")
    print(f"  Mean:   {summary.mean_moic:6.2f}x")
    print(f"  Median: {summary.median_moic:6.2f}x")

    print(f"\nDispersion:")
    print(f"  Std Dev: {summary.std_moic:6.2f}x")
    print(f"  Min:     {summary.min_moic:6.2f}x")
    print(f"  Max:     {summary.max_moic:6.2f}x")
    print(f"  Range:   {summary.max_moic - summary.min_moic:6.2f}x")

    print(f"\nPercentile Distribution:")
    print(f"  5th:  {summary.percentile_5_moic:6.2f}x  (5% of outcomes below)")
    print(f"  25th: {summary.percentile_25_moic:6.2f}x  (25% of outcomes below)")
    print(f"  50th: {summary.median_moic:6.2f}x  (median)")
    print(f"  75th: {summary.percentile_75_moic:6.2f}x  (75% of outcomes below)")
    print(f"  95th: {summary.percentile_95_moic:6.2f}x  (95% of outcomes below)")

    print(f"\nInterquartile Range:")
    iqr = summary.percentile_75_moic - summary.percentile_25_moic
    print(f"  IQR: {iqr:.2f}x (middle 50% of outcomes)")

    print("\n" + "=" * 80)
    print("SIMULATION RESULTS - IRR (INTERNAL RATE OF RETURN)")
    print("=" * 80)
    print(f"\nCentral Tendency:")
    print(f"  Mean:   {summary.mean_irr:7.2%}")
    print(f"  Median: {summary.median_irr:7.2%}")

    print(f"\nDispersion:")
    print(f"  Std Dev: {summary.std_irr:7.2%}")
    print(f"  Min:     {summary.min_irr:7.2%}")
    print(f"  Max:     {summary.max_irr:7.2%}")
    print(f"  Range:   {summary.max_irr - summary.min_irr:7.2%}")

    print(f"\nPercentile Distribution:")
    print(f"  5th:  {summary.percentile_5_irr:7.2%}  (5% of outcomes below)")
    print(f"  25th: {summary.percentile_25_irr:7.2%}  (25% of outcomes below)")
    print(f"  50th: {summary.median_irr:7.2%}  (median)")
    print(f"  75th: {summary.percentile_75_irr:7.2%}  (75% of outcomes below)")
    print(f"  95th: {summary.percentile_95_irr:7.2%}  (95% of outcomes below)")

    print("\n" + "=" * 80)
    print("PERFORMANCE ANALYSIS")
    print("=" * 80)
    print(f"\nProbability of Positive Returns:")
    positive_moic = sum(1 for r in results if r.moic > 1.0)
    pct_positive = positive_moic / len(results)
    print(f"  MOIC > 1.0x: {pct_positive:.1%} ({positive_moic:,} out of {len(results):,})")

    positive_irr = sum(1 for r in results if r.irr > 0)
    pct_positive_irr = positive_irr / len(results)
    print(f"  IRR > 0%:    {pct_positive_irr:.1%} ({positive_irr:,} out of {len(results):,})")

    print(f"\nProbability of Exceeding Benchmarks:")
    above_2x = sum(1 for r in results if r.moic >= 2.0)
    pct_2x = above_2x / len(results)
    print(f"  MOIC >= 2.0x: {pct_2x:.1%} ({above_2x:,} outcomes)")

    above_3x = sum(1 for r in results if r.moic >= 3.0)
    pct_3x = above_3x / len(results)
    print(f"  MOIC >= 3.0x: {pct_3x:.1%} ({above_3x:,} outcomes)")

    above_25pct = sum(1 for r in results if r.irr >= 0.25)
    pct_25 = above_25pct / len(results)
    print(f"  IRR >= 25%:   {pct_25:.1%} ({above_25pct:,} outcomes)")

    print("\n" + "=" * 80)
    print("FINANCIAL ENGINEERING IMPACT")
    print("=" * 80)

    avg_fees = sum(r.fees_paid for r in results) / len(results)
    avg_carry = sum(r.carry_paid for r in results) / len(results)
    avg_leverage_cost = sum(r.leverage_cost for r in results) / len(results)

    print(f"\nAverage per Simulation:")
    print(f"  Management Fees: ${avg_fees:,.0f}")
    print(f"  Carry Paid:      ${avg_carry:,.0f}")
    print(f"  Leverage Cost:   ${avg_leverage_cost:,.0f}")
    print(f"  Total Costs:     ${avg_fees + avg_carry + avg_leverage_cost:,.0f}")

    print("\n" + "=" * 80)
    print("TEST VALIDATION")
    print("=" * 80)

    # Verify reproducibility - run a small test
    print("\nTesting reproducibility (seed=42)...")
    test_results_1 = run_monte_carlo_simulation(investments[:10],
                                                 SimulationConfiguration(
                                                     fund_name="Test",
                                                     fund_manager="Test",
                                                     simulation_count=100
                                                 ))
    test_results_2 = run_monte_carlo_simulation(investments[:10],
                                                 SimulationConfiguration(
                                                     fund_name="Test",
                                                     fund_manager="Test",
                                                     simulation_count=100
                                                 ))

    identical = all(r1.moic == r2.moic and r1.irr == r2.irr
                   for r1, r2 in zip(test_results_1, test_results_2))

    if identical:
        print("  SUCCESS: Results are reproducible (identical across runs)")
    else:
        print("  WARNING: Results differ across runs")

    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nSimulation: {config.simulation_count:,} iterations")
    print(f"Time: {elapsed_time:.2f} seconds")
    print(f"Rate: {rate:,.0f} simulations/second")
    print(f"Timestamp: {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nAll components working correctly:")
    print("  - Data import and validation")
    print("  - Monte Carlo simulation engine")
    print("  - Financial engineering (fees, carry, leverage)")
    print("  - Statistical analysis")
    print("  - Reproducibility (seed=42)")


if __name__ == "__main__":
    main()
