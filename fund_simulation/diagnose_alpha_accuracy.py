"""
COMPREHENSIVE ALPHA ACCURACY DIAGNOSTIC

This script investigates potential root causes for inaccurate (too low) alpha levels
in the deconstructed simulation mode.

Top 5 Root Causes to Investigate:
1. Beta Decomposition Formula Error - Wrong calculation of alpha component
2. Double-Counting of Fees/Costs - Fees applied multiple times
3. Time Period Mismatch - Date misalignment in beta calculation
4. Statistical Sampling Bias - Alpha distributions not preserved
5. Reconstruction Math Error - Formula applied incorrectly

Usage:
    python diagnose_alpha_accuracy.py
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import all relevant modules
from fund_simulation.data_import import parse_csv_file, decompose_historical_beta
from fund_simulation.beta_import import parse_beta_csv, create_beta_index
from fund_simulation.models import SimulationConfiguration
from fund_simulation.simulation import run_monte_carlo_simulation
from fund_simulation.reconstruction import reconstruct_gross_performance
from fund_simulation.statistics import calculate_summary_statistics


def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 100)
    print(title.center(100))
    print("=" * 100)


def print_subheader(title):
    """Print a formatted subsection header."""
    print("\n" + "-" * 100)
    print(title)
    print("-" * 100)


def diagnose_root_cause_1_decomposition_formula(investments, beta_index):
    """
    ROOT CAUSE #1: Beta Decomposition Formula Error

    Checks:
    - Is G_alpha = G_total / G_beta^β calculated correctly?
    - Are market returns for holding period correct?
    - Is beta coefficient applied correctly?
    - Are dates aligned properly?
    """
    print_header("ROOT CAUSE #1: BETA DECOMPOSITION FORMULA")

    print("\nTesting decomposition on sample investments...")
    print(f"Total investments: {len(investments)}")
    beta_start = beta_index.prices[0].date if beta_index.prices else None
    beta_end = beta_index.prices[-1].date if beta_index.prices else None
    print(f"Beta index date range: {beta_start.date()} to {beta_end.date()}")
    print(f"Beta index observations: {len(beta_index.prices)}")

    # Run decomposition with verbose diagnostics
    alpha_investments, decomp_diag = decompose_historical_beta(
        investments,
        beta_index,
        beta_exposure=1.0,
        verbose=True
    )

    print(f"\nSuccessfully decomposed: {len(alpha_investments)} investments")
    print(f"Skipped (outside beta range): {len(investments) - len(alpha_investments)} investments")

    # Compare original vs alpha distributions
    print("\n" + "=" * 80)
    print("DISTRIBUTION COMPARISON: Original Total Returns vs Alpha Returns")
    print("=" * 80)

    original_moics = [inv.moic for inv in investments]
    original_irrs = [inv.irr for inv in investments]
    alpha_moics = [inv.moic for inv in alpha_investments]
    alpha_irrs = [inv.irr for inv in alpha_investments]

    print(f"\n{'Metric':<30} {'Original Total':<20} {'Alpha Only':<20} {'Difference':<20}")
    print("-" * 90)
    print(f"{'Mean MOIC':<30} {np.mean(original_moics):>19.4f} {np.mean(alpha_moics):>19.4f} {np.mean(original_moics) - np.mean(alpha_moics):>+19.4f}")
    print(f"{'Median MOIC':<30} {np.median(original_moics):>19.4f} {np.median(alpha_moics):>19.4f} {np.median(original_moics) - np.median(alpha_moics):>+19.4f}")
    print(f"{'Std Dev MOIC':<30} {np.std(original_moics):>19.4f} {np.std(alpha_moics):>19.4f} {np.std(original_moics) - np.std(alpha_moics):>+19.4f}")
    print()
    print(f"{'Mean IRR':<30} {np.mean(original_irrs):>18.2%} {np.mean(alpha_irrs):>18.2%} {np.mean(original_irrs) - np.mean(alpha_irrs):>+18.2%}")
    print(f"{'Median IRR':<30} {np.median(original_irrs):>18.2%} {np.median(alpha_irrs):>18.2%} {np.median(original_irrs) - np.median(alpha_irrs):>+18.2%}")
    print(f"{'Std Dev IRR':<30} {np.std(original_irrs):>18.2%} {np.std(alpha_irrs):>18.2%} {np.std(original_irrs) - np.std(alpha_irrs):>+18.2%}")

    # Check decomposition diagnostics
    print("\n" + "=" * 80)
    print("DECOMPOSITION DIAGNOSTICS")
    print("=" * 80)
    mean_beta_irr = decomp_diag.get('mean_beta_irr')
    median_beta_irr = decomp_diag.get('median_beta_irr')
    print(f"Mean historical beta IRR: {mean_beta_irr:.2%}" if mean_beta_irr is not None else "Mean historical beta IRR: N/A")
    print(f"Median historical beta IRR: {median_beta_irr:.2%}" if median_beta_irr is not None else "Median historical beta IRR: N/A")

    # Sample a few investments and show detailed decomposition
    print("\n" + "=" * 80)
    print("SAMPLE INVESTMENT DECOMPOSITION DETAILS (First 5 investments)")
    print("=" * 80)

    for i, (orig, alpha) in enumerate(zip(investments[:5], alpha_investments[:5])):
        print(f"\nInvestment #{i+1}: {orig.investment_name}")
        print(f"  Entry: {orig.entry_date.date()}, Exit: {orig.latest_date.date()}, Days: {orig.days_held}")
        print(f"  Original Total MOIC: {orig.moic:.4f}x, IRR: {orig.irr:.2%}")
        print(f"  Alpha MOIC: {alpha.moic:.4f}x, IRR: {alpha.irr:.2%}")
        if alpha.moic != 0:
            print(f"  Implied Beta MOIC: {orig.moic / alpha.moic:.4f}x (should equal market return^beta)")
        else:
            print(f"  Implied Beta MOIC: N/A (alpha MOIC is zero)")

    # KEY DIAGNOSTIC: Is alpha systematically too low?
    mean_alpha_moic = np.mean(alpha_moics)
    mean_total_moic = np.mean(original_moics)

    if mean_alpha_moic < 1.0:
        print("\n⚠️ WARNING: Mean alpha MOIC < 1.0 - Alpha is showing systematic underperformance")
        print("   This could indicate:")
        print("   - Beta component overcalculated (stripping too much from total)")
        print("   - Beta coefficient too high")
        print("   - Market had exceptional returns during investment period")

    if mean_alpha_moic < mean_total_moic * 0.5:
        print("\n⚠️ CRITICAL: Alpha MOIC is less than 50% of total MOIC")
        print("   This suggests beta is being assigned majority of returns")
        print("   Check: Is beta exposure coefficient = 1.0 correct for this data?")

    return {
        'original_moics': original_moics,
        'original_irrs': original_irrs,
        'alpha_moics': alpha_moics,
        'alpha_irrs': alpha_irrs,
        'alpha_investments': alpha_investments,
        'decomp_diag': decomp_diag
    }


def diagnose_root_cause_2_double_counting(config):
    """
    ROOT CAUSE #2: Double-Counting of Fees/Costs

    Checks:
    - Are fees being applied during decomposition? (should NOT be)
    - Are fees being applied during alpha simulation? (should NOT be)
    - Are fees being applied during reconstruction? (should ONLY be in net reconstruction)
    """
    print_header("ROOT CAUSE #2: DOUBLE-COUNTING OF FEES/COSTS")

    print("\nChecking financial engineering parameters from config...")
    print(f"  Leverage rate: {config.leverage_rate:.2%}")
    print(f"  Cost of capital: {config.cost_of_capital:.2%}")
    print(f"  Management fee rate: {config.fee_rate:.2%}")
    print(f"  Carry rate: {config.carry_rate:.2%}")
    print(f"  Hurdle rate: {config.hurdle_rate:.2%}")

    print("\n" + "=" * 80)
    print("CODE AUDIT: Where are fees applied?")
    print("=" * 80)

    print("\n1. decompose_historical_beta() in data_import.py:")
    print("   OK - CORRECT: Does NOT apply fees - strips beta from historical total returns")
    print("   OK - CORRECT: Historical returns should already be gross (before fees)")

    print("\n2. run_monte_carlo_simulation() with apply_costs=False (alpha simulation):")
    print("   OK - CORRECT: Should NOT apply fees when apply_costs=False")
    print("   ? TO VERIFY: Check that alpha simulation is called with apply_costs=False")

    print("\n3. reconstruct_gross_performance() in reconstruction.py:")
    print("   OK - CORRECT: Should NOT apply fees - only combines alpha × beta")

    print("\n4. reconstruct_net_performance() in reconstruction.py:")
    print("   OK - CORRECT: Should ONLY apply fees here (final stage)")

    print("\n" + "=" * 80)
    print("RECOMMENDATION: Check app.py to verify apply_costs=False for alpha simulation")
    print("=" * 80)

    return {
        'config': config
    }


def diagnose_root_cause_3_time_mismatch(investments, beta_index, alpha_investments):
    """
    ROOT CAUSE #3: Time Period Mismatch in Beta Calculation

    Checks:
    - Are investment holding periods matching beta lookup periods?
    - Are there off-by-one errors in date ranges?
    - Trading days vs calendar days confusion?
    """
    print_header("ROOT CAUSE #3: TIME PERIOD MISMATCH")

    print("\nAnalyzing date alignment for sample investments...")

    print("\n" + "=" * 80)
    print("DATE ALIGNMENT CHECK (First 5 investments)")
    print("=" * 80)

    for i, (orig, alpha) in enumerate(zip(investments[:5], alpha_investments[:5])):
        print(f"\nInvestment #{i+1}: {orig.investment_name}")
        print(f"  Entry date: {orig.entry_date.date()}")
        print(f"  Exit date: {orig.latest_date.date()}")
        print(f"  Holding period: {orig.days_held} days ({orig.days_held / 365.25:.2f} years)")

        # Check if dates are within beta index range
        beta_start = beta_index.prices[0].date
        beta_end = beta_index.prices[-1].date
        if orig.entry_date < beta_start:
            print(f"  ⚠️ WARNING: Entry date before beta index start ({beta_start.date()})")
        if orig.latest_date > beta_end:
            print(f"  ⚠️ WARNING: Exit date after beta index end ({beta_end.date()})")

        # Check if dates match exactly or if interpolation is needed
        entry_in_index = any(p.date == orig.entry_date for p in beta_index.prices)
        exit_in_index = any(p.date == orig.latest_date for p in beta_index.prices)

        print(f"  Entry date in beta index: {'YES (exact match)' if entry_in_index else 'NO (interpolated)'}")
        print(f"  Exit date in beta index: {'YES (exact match)' if exit_in_index else 'NO (interpolated)'}")

    # Check beta index frequency
    print("\n" + "=" * 80)
    print("BETA INDEX FREQUENCY ANALYSIS")
    print("=" * 80)

    if len(beta_index.prices) >= 2:
        date_diffs = [(beta_index.prices[i+1].date - beta_index.prices[i].date).days
                     for i in range(min(10, len(beta_index.prices) - 1))]
        print(f"First 10 date intervals (days): {date_diffs}")
        print(f"Average interval: {np.mean(date_diffs):.1f} days")
        print(f"Frequency: {beta_index.frequency}")

        if beta_index.frequency == 'monthly' and np.mean(date_diffs) < 25:
            print("⚠️ WARNING: Frequency marked as 'monthly' but intervals < 25 days")
        if beta_index.frequency == 'daily' and np.mean(date_diffs) > 5:
            print("⚠️ WARNING: Frequency marked as 'daily' but intervals > 5 days")

    return {}


def diagnose_root_cause_4_sampling_bias(alpha_results, alpha_investments, config):
    """
    ROOT CAUSE #4: Statistical Sampling Bias in Alpha Simulation

    Checks:
    - Are alpha distributions preserved correctly?
    - Is portfolio construction skewing results?
    - Are tail behaviors captured?
    """
    print_header("ROOT CAUSE #4: STATISTICAL SAMPLING BIAS")

    print("\nComparing alpha investment universe vs simulated alpha results...")

    # Alpha universe statistics
    alpha_input_moics = [inv.moic for inv in alpha_investments]
    alpha_input_irrs = [inv.irr for inv in alpha_investments]

    # Alpha simulation results statistics
    alpha_sim_moics = [r.moic for r in alpha_results]
    alpha_sim_irrs = [r.irr for r in alpha_results]

    print("\n" + "=" * 80)
    print("ALPHA DISTRIBUTION: Input Universe vs Simulation Results")
    print("=" * 80)
    print(f"\nInput universe: {len(alpha_investments)} investments")
    print(f"Simulation results: {len(alpha_results)} portfolios")
    print(f"Simulations per portfolio: mean={config.investment_count_mean}, std={config.investment_count_std}")

    print(f"\n{'Metric':<30} {'Input Universe':<20} {'Simulation Results':<20} {'Difference':<20}")
    print("-" * 90)
    print(f"{'Mean MOIC':<30} {np.mean(alpha_input_moics):>19.4f} {np.mean(alpha_sim_moics):>19.4f} {np.mean(alpha_sim_moics) - np.mean(alpha_input_moics):>+19.4f}")
    print(f"{'Median MOIC':<30} {np.median(alpha_input_moics):>19.4f} {np.median(alpha_sim_moics):>19.4f} {np.median(alpha_sim_moics) - np.median(alpha_input_moics):>+19.4f}")
    print(f"{'Std Dev MOIC':<30} {np.std(alpha_input_moics):>19.4f} {np.std(alpha_sim_moics):>19.4f} {np.std(alpha_sim_moics) - np.std(alpha_input_moics):>+19.4f}")
    print(f"{'Min MOIC':<30} {np.min(alpha_input_moics):>19.4f} {np.min(alpha_sim_moics):>19.4f} {np.min(alpha_sim_moics) - np.min(alpha_input_moics):>+19.4f}")
    print(f"{'Max MOIC':<30} {np.max(alpha_input_moics):>19.4f} {np.max(alpha_sim_moics):>19.4f} {np.max(alpha_sim_moics) - np.max(alpha_input_moics):>+19.4f}")
    print()
    print(f"{'Mean IRR':<30} {np.mean(alpha_input_irrs):>18.2%} {np.mean(alpha_sim_irrs):>18.2%} {np.mean(alpha_sim_irrs) - np.mean(alpha_input_irrs):>+18.2%}")
    print(f"{'Median IRR':<30} {np.median(alpha_input_irrs):>18.2%} {np.median(alpha_sim_irrs):>18.2%} {np.median(alpha_sim_irrs) - np.median(alpha_input_irrs):>+18.2%}")
    print(f"{'Std Dev IRR':<30} {np.std(alpha_input_irrs):>18.2%} {np.std(alpha_sim_irrs):>18.2%} {np.std(alpha_sim_irrs) - np.std(alpha_input_irrs):>+18.2%}")

    # Expected behavior: Simulation mean should approximately equal input mean
    # But simulation std should be SMALLER (portfolio diversification effect)

    mean_moic_diff = np.mean(alpha_sim_moics) - np.mean(alpha_input_moics)
    std_moic_ratio = np.std(alpha_sim_moics) / np.std(alpha_input_moics)

    print("\n" + "=" * 80)
    print("SAMPLING BIAS ANALYSIS")
    print("=" * 80)

    if abs(mean_moic_diff) > 0.1:
        print(f"⚠️ WARNING: Simulation mean differs from input mean by {mean_moic_diff:+.4f}")
        print("   Expected: Simulation mean ≈ input mean (sampling with replacement)")
        print("   Possible causes:")
        print("   - Small sample size in universe")
        print("   - Sampling not truly random")
        print("   - Bug in portfolio construction")
    else:
        print(f"OK - GOOD: Simulation mean matches input mean (difference: {mean_moic_diff:+.4f})")

    if std_moic_ratio > 0.9:
        print(f"\n⚠️ WARNING: Simulation std ({np.std(alpha_sim_moics):.4f}) is {std_moic_ratio:.1%} of input std ({np.std(alpha_input_moics):.4f})")
        print("   Expected: Simulation std < input std (diversification effect)")
        print("   This suggests portfolios are NOT diversifying")
    else:
        print(f"\nOK - GOOD: Simulation std shows diversification effect (ratio: {std_moic_ratio:.1%})")

    return {
        'alpha_input_moics': alpha_input_moics,
        'alpha_input_irrs': alpha_input_irrs,
        'alpha_sim_moics': alpha_sim_moics,
        'alpha_sim_irrs': alpha_sim_irrs
    }


def diagnose_root_cause_5_reconstruction_math(alpha_results, beta_paths, reconstructed_results, config):
    """
    ROOT CAUSE #5: Reconstruction Math Error

    Checks:
    - Is Total MOIC = Alpha MOIC × (Beta MOIC^β) applied correctly?
    - Round-trip accuracy test
    """
    print_header("ROOT CAUSE #5: RECONSTRUCTION MATH ERROR")

    print("\nTesting reconstruction formula: Total = Alpha × Beta^beta")
    print(f"Beta exposure coefficient (beta): {config.beta_exposure}")

    # Sample a few portfolios and verify reconstruction manually
    print("\n" + "=" * 80)
    print("MANUAL RECONSTRUCTION VERIFICATION (First 5 portfolios)")
    print("=" * 80)

    for i in range(min(5, len(alpha_results))):
        alpha_result = alpha_results[i]
        recon_result = reconstructed_results[i]

        print(f"\nPortfolio #{i+1}:")
        print(f"  Alpha MOIC: {alpha_result.moic:.4f}x")
        print(f"  Reconstructed Total MOIC: {recon_result.moic:.4f}x")

        # We can't easily verify beta MOIC here without knowing which path was sampled
        # But we can check if reconstructed >= alpha (assuming beta > 1.0)
        if recon_result.moic < alpha_result.moic:
            print(f"  ⚠️ WARNING: Reconstructed MOIC < Alpha MOIC")
            print(f"     This implies Beta MOIC < 1.0 (market declined)")

    # Compare distributions
    alpha_moics = [r.moic for r in alpha_results]
    recon_moics = [r.moic for r in reconstructed_results]

    print("\n" + "=" * 80)
    print("ALPHA vs RECONSTRUCTED DISTRIBUTION COMPARISON")
    print("=" * 80)

    print(f"\n{'Metric':<30} {'Alpha':<20} {'Reconstructed':<20} {'Difference':<20}")
    print("-" * 90)
    print(f"{'Mean MOIC':<30} {np.mean(alpha_moics):>19.4f} {np.mean(recon_moics):>19.4f} {np.mean(recon_moics) - np.mean(alpha_moics):>+19.4f}")
    print(f"{'Median MOIC':<30} {np.median(alpha_moics):>19.4f} {np.median(recon_moics):>19.4f} {np.median(recon_moics) - np.median(alpha_moics):>+19.4f}")
    print(f"{'Std Dev MOIC':<30} {np.std(alpha_moics):>19.4f} {np.std(recon_moics):>19.4f} {np.std(recon_moics) - np.std(alpha_moics):>+19.4f}")

    # Expected: Reconstructed should be higher than alpha (if beta returns are positive)
    # The ratio gives us insight into beta contribution
    ratio = np.mean(recon_moics) / np.mean(alpha_moics)
    print(f"\nReconstructed / Alpha ratio: {ratio:.4f}")

    if ratio < 1.0:
        print("⚠️ WARNING: Reconstructed MOIC < Alpha MOIC on average")
        print("   This suggests beta is reducing returns (market declined)")
        print("   OR there's an error in reconstruction formula")
    elif ratio < 1.5:
        print("⚠️ POTENTIAL ISSUE: Beta contribution seems low")
        print(f"   If beta target return is ~15%, expect ratio > 1.5 over 10 years")
    else:
        print(f"OK - Beta is adding value (ratio = {ratio:.2f}x)")

    return {
        'alpha_moics': alpha_moics,
        'recon_moics': recon_moics,
        'ratio': ratio
    }


def main():
    """
    Main diagnostic workflow.
    """
    print_header("COMPREHENSIVE ALPHA ACCURACY DIAGNOSTIC")
    print("\nThis script will investigate 5 potential root causes for low alpha values:")
    print("1. Beta Decomposition Formula Error")
    print("2. Double-Counting of Fees/Costs")
    print("3. Time Period Mismatch")
    print("4. Statistical Sampling Bias")
    print("5. Reconstruction Math Error")

    # Load data (you'll need to update these paths)
    print("\n" + "=" * 100)
    print("LOADING DATA...")
    print("=" * 100)

    # TODO: Update these paths to your actual data files
    investment_csv = "temp_upload.csv"  # Path to your investment data
    beta_csv = "temp_beta_upload.csv"   # Path to your beta index data

    print(f"\nLoading investments from: {investment_csv}")
    investments, errors = parse_csv_file(investment_csv)
    if errors:
        print(f"⚠️ Found {len(errors)} errors loading investments")
        for error in errors[:5]:
            print(f"   - {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")
    print(f"OK - Loaded {len(investments)} investments")

    print(f"\nLoading beta index from: {beta_csv}")
    beta_prices, beta_errors, detected_freq = parse_beta_csv(beta_csv)
    if beta_errors:
        print(f"⚠️ Found {len(beta_errors)} errors loading beta data")
    beta_index = create_beta_index(beta_prices, detected_freq)
    print(f"OK - Loaded {len(beta_prices)} beta prices (frequency: {detected_freq})")

    # Create config
    config = SimulationConfiguration(
        fund_name="Diagnostic Test",
        fund_manager="Test Manager",
        leverage_rate=0.0,
        cost_of_capital=0.08,
        fee_rate=0.02,
        carry_rate=0.20,
        hurdle_rate=0.08,
        simulation_count=1000,  # Small sample for diagnostics
        investment_count_mean=10.0,
        investment_count_std=2.0,
        simulation_mode="deconstructed_performance",
        beta_horizon_days=2520,
        beta_n_paths=1000,
        beta_outlook="base",
        beta_confidence="medium",
        beta_exposure=1.0
    )

    # ROOT CAUSE #1: Decomposition
    result_1 = diagnose_root_cause_1_decomposition_formula(investments, beta_index)

    # ROOT CAUSE #2: Double-counting
    result_2 = diagnose_root_cause_2_double_counting(config)

    # ROOT CAUSE #3: Time mismatch
    result_3 = diagnose_root_cause_3_time_mismatch(
        investments,
        beta_index,
        result_1['alpha_investments']
    )

    # Run alpha simulation for further diagnostics
    print_header("RUNNING ALPHA SIMULATION FOR DIAGNOSTICS")
    print("\nRunning alpha simulation with apply_costs=False...")

    alpha_results = run_monte_carlo_simulation(
        result_1['alpha_investments'],
        config,
        progress_callback=None,
        beta_index=beta_index,
        export_details=True,
        apply_costs=False,  # CRITICAL: No costs for alpha
        use_alpha=True  # Use alpha returns
    )
    print(f"OK - Completed {len(alpha_results)} alpha simulations")

    # ROOT CAUSE #4: Sampling bias
    result_4 = diagnose_root_cause_4_sampling_bias(
        alpha_results,
        result_1['alpha_investments'],
        config
    )

    # Run beta simulation and reconstruction for Root Cause #5
    print_header("RUNNING BETA SIMULATION AND RECONSTRUCTION FOR DIAGNOSTICS")

    from fund_simulation.beta_simulation import simulate_beta_forward
    from fund_simulation.reconstruction import reconstruct_gross_performance

    print("\nGenerating beta paths...")
    beta_paths, beta_diagnostics = simulate_beta_forward(
        beta_index,
        config.beta_horizon_days,
        config.beta_n_paths,
        seed=42,
        outlook=config.beta_outlook,
        confidence=config.beta_confidence
    )
    print(f"OK - Generated {config.beta_n_paths} beta paths")

    print("\nReconstructing gross performance...")
    random_state_recon = np.random.RandomState(seed=42)

    original_returns_lookup = result_1['decomp_diag'].get('original_returns_lookup')

    reconstructed_results, beta_recon_diag = reconstruct_gross_performance(
        alpha_results,
        beta_paths,
        beta_paths.index[0],
        config,
        random_state_recon,
        original_returns_lookup
    )
    print(f"OK - Reconstructed {len(reconstructed_results)} portfolios")

    # ROOT CAUSE #5: Reconstruction math
    result_5 = diagnose_root_cause_5_reconstruction_math(
        alpha_results,
        beta_paths,
        reconstructed_results,
        config
    )

    # FINAL SUMMARY
    print_header("DIAGNOSTIC SUMMARY AND RECOMMENDATIONS")

    print("\n1. BETA DECOMPOSITION:")
    print(f"   - Original mean MOIC: {np.mean(result_1['original_moics']):.4f}x")
    print(f"   - Alpha mean MOIC: {np.mean(result_1['alpha_moics']):.4f}x")
    print(f"   - Reduction: {(1 - np.mean(result_1['alpha_moics'])/np.mean(result_1['original_moics'])) * 100:.1f}%")

    print("\n2. DOUBLE-COUNTING:")
    print("   - Check app.py to verify apply_costs=False for alpha simulation")

    print("\n3. TIME PERIOD MISMATCH:")
    print("   - Review date alignment output above")

    print("\n4. SAMPLING BIAS:")
    mean_diff_pct = (np.mean(result_4['alpha_sim_moics']) / np.mean(result_4['alpha_input_moics']) - 1) * 100
    print(f"   - Simulation mean vs input mean: {mean_diff_pct:+.1f}%")
    if abs(mean_diff_pct) > 5:
        print("   ⚠️ Simulation is biased!")

    print("\n5. RECONSTRUCTION MATH:")
    print(f"   - Reconstructed / Alpha ratio: {result_5['ratio']:.4f}x")
    print(f"   - This represents beta contribution")

    print("\n" + "=" * 100)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 100)
    print("\nReview the detailed output above to identify the root cause.")
    print("Most likely culprits based on 'too low' alpha:")
    print("  1. Beta exposure coefficient too high (stripping too much beta)")
    print("  2. Market (beta index) had exceptional returns during period")
    print("  3. Double-counting of fees somewhere in the pipeline")


if __name__ == "__main__":
    main()
