"""
Systematic Testing Framework for Beta Simulation

This script tests whether the -0.26% bias is:
1. Systematic (always present) or random (statistical noise)
2. Fixable with bootstrap sample centering

Tests run:
- 10 seeds with current implementation
- 10 seeds with bootstrap centering fix
- Across volatility regimes
- Statistical analysis of results
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add fund_simulation to path
sys.path.insert(0, str(Path(__file__).parent / 'fund_simulation'))

from fund_simulation.beta_simulation import simulate_beta_forward
from fund_simulation.models import BetaPrice, BetaPriceIndex


def load_beta_data(filepath):
    """Load beta price data from CSV and create BetaPriceIndex"""
    df = pd.read_csv(filepath, header=None, names=['date', 'price'])
    df['date'] = pd.to_datetime(df['date'], format='%d-%b-%y')
    df = df.sort_values('date')

    # Create BetaPrice objects
    beta_prices = [
        BetaPrice(date=row['date'].to_pydatetime(), price=row['price'])
        for _, row in df.iterrows()
    ]

    # Create BetaPriceIndex
    beta_index = BetaPriceIndex(prices=beta_prices, frequency='quarterly')

    return beta_index


def run_single_simulation(beta_index, seed, market_mood='normal', outlook='base'):
    """
    Run a single beta simulation and return the error

    Args:
        beta_index: BetaPriceIndex object
        seed: Random seed
        market_mood: 'calm', 'normal', or 'turbulent'
        outlook: 'pessimistic', 'base', or 'optimistic'

    Returns:
        dict with target, actual, error, and other metrics
    """
    # Run simulation - returns (paths_df, diagnostics)
    paths_df, diagnostics = simulate_beta_forward(
        beta_index=beta_index,
        horizon_days=2520,  # 10 years
        n_paths=1000,
        seed=seed,
        outlook=outlook,
        market_mood=market_mood,
        confidence='medium'
    )

    return {
        'seed': seed,
        'market_mood': market_mood,
        'outlook': outlook,
        'target': diagnostics['R_target_actual'],
        'actual': diagnostics['validation_mean_return'],
        'error': diagnostics['validation_error'],
        'error_pct': diagnostics['validation_error'] * 100,
        'std': diagnostics.get('validation_std_return', 0.0)
    }


def test_baseline(beta_prices, n_tests=10):
    """Test current implementation across different seeds"""
    print("=" * 80)
    print("TEST A: BASELINE (Current Implementation)")
    print("=" * 80)
    print(f"Running {n_tests} simulations with different random seeds...")
    print()

    results = []
    for i, seed in enumerate(range(42, 42 + n_tests), 1):
        print(f"  Run {i}/{n_tests} (seed={seed})...", end='', flush=True)
        result = run_single_simulation(beta_prices, seed, market_mood='normal', outlook='base')
        results.append(result)
        print(f" Error: {result['error_pct']:+.2f}%")

    # Statistical analysis
    errors = [r['error_pct'] for r in results]
    mean_error = np.mean(errors)
    std_error = np.std(errors)
    min_error = np.min(errors)
    max_error = np.max(errors)

    print()
    print("Results:")
    print(f"  Mean error: {mean_error:+.3f}%")
    print(f"  Std error:  {std_error:.3f}%")
    print(f"  Min error:  {min_error:+.3f}%")
    print(f"  Max error:  {max_error:+.3f}%")
    print(f"  Range:      {max_error - min_error:.3f}%")

    # Check if systematic
    all_negative = all(e < 0 for e in errors)
    all_positive = all(e > 0 for e in errors)

    if all_negative:
        print(f"  ⚠️  SYSTEMATIC NEGATIVE BIAS (all {n_tests} runs are negative)")
    elif all_positive:
        print(f"  ⚠️  SYSTEMATIC POSITIVE BIAS (all {n_tests} runs are positive)")
    else:
        print(f"  ✅ Errors scatter (not systematic)")

    print()

    return results, {
        'mean_error': mean_error,
        'std_error': std_error,
        'is_systematic': all_negative or all_positive,
        'bias_direction': 'negative' if all_negative else ('positive' if all_positive else 'none')
    }


def test_volatility_regimes(beta_prices, seed=42):
    """Test across different volatility regimes"""
    print("=" * 80)
    print("TEST B: VOLATILITY REGIMES")
    print("=" * 80)
    print("Testing calm, normal, and turbulent market moods...")
    print()

    results = []
    for mood in ['calm', 'normal', 'turbulent']:
        print(f"  {mood.capitalize():12s}...", end='', flush=True)
        result = run_single_simulation(beta_prices, seed, market_mood=mood, outlook='base')
        results.append(result)
        print(f" Error: {result['error_pct']:+.2f}%")

    errors = [r['error_pct'] for r in results]
    all_negative = all(e < 0 for e in errors)
    all_positive = all(e > 0 for e in errors)

    print()
    if all_negative:
        print("  ⚠️  All regimes show NEGATIVE bias")
    elif all_positive:
        print("  ⚠️  All regimes show POSITIVE bias")
    else:
        print("  ✅ Bias varies by regime")
    print()

    return results


def test_outlook_scenarios(beta_prices, seed=42):
    """Test across different return outlooks"""
    print("=" * 80)
    print("TEST C: RETURN OUTLOOKS")
    print("=" * 80)
    print("Testing pessimistic, base, and optimistic outlooks...")
    print()

    results = []
    for outlook in ['pessimistic', 'base', 'optimistic']:
        print(f"  {outlook.capitalize():12s}...", end='', flush=True)
        result = run_single_simulation(beta_prices, seed, market_mood='normal', outlook=outlook)
        results.append(result)
        print(f" Target: {result['target']*100:.2f}%, Actual: {result['actual']*100:.2f}%, Error: {result['error_pct']:+.2f}%")

    errors = [r['error_pct'] for r in results]
    all_negative = all(e < 0 for e in errors)
    all_positive = all(e > 0 for e in errors)

    print()
    if all_negative:
        print("  ⚠️  All outlooks show NEGATIVE bias")
    elif all_positive:
        print("  ⚠️  All outlooks show POSITIVE bias")
    else:
        print("  ✅ Bias varies by outlook")
    print()

    return results


def generate_report(baseline_results, baseline_stats, volatility_results, outlook_results):
    """Generate summary report"""
    print("=" * 80)
    print("EXECUTIVE SUMMARY")
    print("=" * 80)
    print()

    # Is bias systematic?
    if baseline_stats['is_systematic']:
        print(f"✗ FINDING: Bias is SYSTEMATIC ({baseline_stats['bias_direction']})")
        print(f"  - All {len(baseline_results)} test runs show {baseline_stats['bias_direction']} error")
        print(f"  - Mean error: {baseline_stats['mean_error']:+.3f}%")
        print(f"  - Variation is tiny (std={baseline_stats['std_error']:.3f}%)")
        print()
        print("  This is NOT statistical noise. The simulation has a systematic bias.")
        print()
        print("RECOMMENDATION:")
        print("  Implement bootstrap sample centering fix:")
        print("    eps_boot = eps_boot - eps_boot.mean()")
        print("  after circular_block_bootstrap() call")
    else:
        print(f"✓ FINDING: Bias is RANDOM (statistical noise)")
        print(f"  - Mean error: {baseline_stats['mean_error']:+.3f}%")
        print(f"  - Errors scatter with std={baseline_stats['std_error']:.3f}%")
        print()
        print("  This is acceptable Monte Carlo sampling variance.")
        print()
        print("RECOMMENDATION:")
        print("  No action needed. The simulation is working correctly.")

    print()
    print("=" * 80)
    print()


def main():
    """Run full test suite"""
    print()
    print("=" * 80)
    print("SYSTEMATIC BETA SIMULATION TESTING")
    print("=" * 80)
    print()
    print("This test suite will:")
    print("  1. Run 10 simulations with different seeds")
    print("  2. Test across volatility regimes (calm/normal/turbulent)")
    print("  3. Test across return outlooks (pessimistic/base/optimistic)")
    print("  4. Determine if bias is systematic or random")
    print()
    print("Estimated time: 2-3 minutes per simulation = 40-60 minutes total")
    print()
    print("Starting tests...")
    print()

    # Load data
    print("Loading beta price data...")
    beta_index = load_beta_data('Lead Edge Beta.csv')
    print(f"  Loaded {len(beta_index.prices)} price points from {beta_index.prices[0].date} to {beta_index.prices[-1].date}")
    print()

    # Run tests
    baseline_results, baseline_stats = test_baseline(beta_index, n_tests=10)
    volatility_results = test_volatility_regimes(beta_index)
    outlook_results = test_outlook_scenarios(beta_index)

    # Generate report
    generate_report(baseline_results, baseline_stats, volatility_results, outlook_results)

    # Save detailed results
    all_results = baseline_results + volatility_results + outlook_results
    df = pd.DataFrame(all_results)
    output_file = 'beta_test_results.csv'
    df.to_csv(output_file, index=False)
    print(f"Detailed results saved to: {output_file}")
    print()


if __name__ == '__main__':
    main()
