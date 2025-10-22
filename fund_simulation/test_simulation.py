"""Test simulation with real Lead Edge data"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fund_simulation.data_import import parse_csv_file
from fund_simulation.models import SimulationConfiguration
from fund_simulation.simulation import run_monte_carlo_simulation
from fund_simulation.statistics import calculate_summary_statistics


def main():
    print("=" * 70)
    print("Monte Carlo Fund Simulation - Test Run")
    print("=" * 70)

    # Load Lead Edge data
    csv_path = "../Lead Edge Deals.csv"
    print(f"\nLoading data from: {csv_path}")

    investments, errors = parse_csv_file(csv_path)

    if errors:
        print(f"\nWARNING: Found {len(errors)} error(s):")
        for error in errors[:5]:
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")

    if not investments:
        print("\nERROR: No investments loaded. Exiting.")
        return

    print(f"\nSUCCESS: Successfully loaded {len(investments)} investments")

    # Show sample data
    print("\nSample investments:")
    for inv in investments[:5]:
        print(f"  {inv.investment_name} ({inv.fund_name}): {inv.moic:.2f}x MOIC, {inv.irr:.2%} IRR")

    # Create configuration
    config = SimulationConfiguration(
        fund_name="Lead Edge Simulated Fund",
        fund_manager="Lead Edge Capital",
        leverage_rate=0.0,  # No leverage
        cost_of_capital=0.08,
        fee_rate=0.02,
        carry_rate=0.20,
        hurdle_rate=0.08,
        simulation_count=1000,  # Small test run
        investment_count_mean=15.0,
        investment_count_std=3.0
    )

    # Validate configuration
    errors = config.validate()
    if errors:
        print("\nERROR: Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return

    print("\nSUCCESS: Configuration is valid")
    print(f"\nRunning {config.simulation_count:,} simulations...")

    # Run simulation
    progress_count = [0]

    def show_progress(fraction):
        current = int(fraction * config.simulation_count)
        if current > progress_count[0]:
            progress_count[0] = current
            print(f"  Progress: {fraction*100:.1f}% ({current:,}/{config.simulation_count:,})")

    results = run_monte_carlo_simulation(
        investments,
        config,
        progress_callback=show_progress
    )

    print(f"\nSUCCESS: Completed {len(results):,} simulations")

    # Calculate statistics
    summary = calculate_summary_statistics(results, config)

    # Display results
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)

    print("\nMOIC Statistics:")
    print(f"  Mean:           {summary.mean_moic:.2f}x")
    print(f"  Median:         {summary.median_moic:.2f}x")
    print(f"  Std Dev:        {summary.std_moic:.2f}x")
    print(f"  Min:            {summary.min_moic:.2f}x")
    print(f"  Max:            {summary.max_moic:.2f}x")
    print(f"  5th Percentile: {summary.percentile_5_moic:.2f}x")
    print(f"  25th Percentile:{summary.percentile_25_moic:.2f}x")
    print(f"  75th Percentile:{summary.percentile_75_moic:.2f}x")
    print(f"  95th Percentile:{summary.percentile_95_moic:.2f}x")

    print("\nIRR Statistics:")
    print(f"  Mean:           {summary.mean_irr:.2%}")
    print(f"  Median:         {summary.median_irr:.2%}")
    print(f"  Std Dev:        {summary.std_irr:.2%}")
    print(f"  Min:            {summary.min_irr:.2%}")
    print(f"  Max:            {summary.max_irr:.2%}")
    print(f"  5th Percentile: {summary.percentile_5_irr:.2%}")
    print(f"  25th Percentile:{summary.percentile_25_irr:.2%}")
    print(f"  75th Percentile:{summary.percentile_75_irr:.2%}")
    print(f"  95th Percentile:{summary.percentile_95_irr:.2%}")

    print("\n" + "=" * 70)
    print("SUCCESS: Test completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
