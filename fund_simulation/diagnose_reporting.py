"""
Non-invasive diagnostic to compare calculated statistics vs reported statistics.

This helps identify discrepancies between what the backend calculates and what
the UI displays, without modifying any data.
"""

import numpy as np


def diagnose_statistics_reporting(
    alpha_results,
    alpha_summary,
    reconstructed_gross_results,
    reconstructed_gross_summary,
    beta_recon_diagnostics
):
    """
    Compare raw calculated statistics with reported summary statistics.

    Args:
        alpha_results: Raw alpha simulation results
        alpha_summary: Summary statistics object for alpha
        reconstructed_gross_results: Raw reconstruction results
        reconstructed_gross_summary: Summary statistics object for reconstruction
        beta_recon_diagnostics: Beta diagnostics from reconstruction

    Returns:
        Dict with discrepancies found
    """
    print("\n" + "=" * 120)
    print("STATISTICS REPORTING DIAGNOSTIC")
    print("=" * 120)
    print()
    print("Comparing raw calculated values vs reported summary statistics...")
    print()

    discrepancies = []

    # =========================================================================
    # ALPHA STATISTICS
    # =========================================================================
    print("=" * 120)
    print("ALPHA STATISTICS (Excess Returns)")
    print("=" * 120)
    print()

    # Calculate directly from results
    alpha_irrs = np.array([r.irr for r in alpha_results if r.irr is not None])
    alpha_moics = np.array([r.moic for r in alpha_results if r.moic is not None])

    calc_alpha_mean_irr = np.mean(alpha_irrs)
    calc_alpha_median_irr = np.median(alpha_irrs)
    calc_alpha_mean_moic = np.mean(alpha_moics)
    calc_alpha_median_moic = np.median(alpha_moics)

    print(f"{'Metric':<30} | {'Calculated (Raw)':<20} | {'Reported (UI)':<20} | {'Match?':<10}")
    print("-" * 120)

    # Mean IRR
    match = abs(calc_alpha_mean_irr - alpha_summary.mean_irr) < 0.0001
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Alpha Mean IRR':<30} | {calc_alpha_mean_irr:>19.4%} | {alpha_summary.mean_irr:>19.4%} | {status:<10}")
    if not match:
        discrepancies.append(("Alpha Mean IRR", calc_alpha_mean_irr, alpha_summary.mean_irr))

    # Median IRR
    match = abs(calc_alpha_median_irr - alpha_summary.median_irr) < 0.0001
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Alpha Median IRR':<30} | {calc_alpha_median_irr:>19.4%} | {alpha_summary.median_irr:>19.4%} | {status:<10}")
    if not match:
        discrepancies.append(("Alpha Median IRR", calc_alpha_median_irr, alpha_summary.median_irr))

    # Mean MOIC
    match = abs(calc_alpha_mean_moic - alpha_summary.mean_moic) < 0.01
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Alpha Mean MOIC':<30} | {calc_alpha_mean_moic:>18.4f}x | {alpha_summary.mean_moic:>18.4f}x | {status:<10}")
    if not match:
        discrepancies.append(("Alpha Mean MOIC", calc_alpha_mean_moic, alpha_summary.mean_moic))

    # Median MOIC
    match = abs(calc_alpha_median_moic - alpha_summary.median_moic) < 0.01
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Alpha Median MOIC':<30} | {calc_alpha_median_moic:>18.4f}x | {alpha_summary.median_moic:>18.4f}x | {status:<10}")
    if not match:
        discrepancies.append(("Alpha Median MOIC", calc_alpha_median_moic, alpha_summary.median_moic))

    print()

    # =========================================================================
    # BETA STATISTICS (from reconstruction)
    # =========================================================================
    print("=" * 120)
    print("BETA STATISTICS (from Reconstruction)")
    print("=" * 120)
    print()

    # Calculate directly from investment details
    all_beta_irrs = []
    all_beta_moics = []

    for result in reconstructed_gross_results:
        if result.investment_details:
            for inv in result.investment_details:
                if inv.beta_irr is not None and inv.days_held >= 30:
                    all_beta_irrs.append(inv.beta_irr)
                    all_beta_moics.append(inv.beta_moic)

    calc_beta_mean_irr = np.mean(all_beta_irrs) if all_beta_irrs else 0
    calc_beta_median_irr = np.median(all_beta_irrs) if all_beta_irrs else 0
    calc_beta_mean_moic = np.mean(all_beta_moics) if all_beta_moics else 0

    reported_beta_mean_irr = beta_recon_diagnostics.get('mean_beta_irr', 0)
    reported_beta_median_irr = beta_recon_diagnostics.get('median_beta_irr', 0)
    reported_beta_mean_moic = beta_recon_diagnostics.get('mean_beta_moic', 0)

    print(f"{'Metric':<30} | {'Calculated (Raw)':<20} | {'Reported (UI)':<20} | {'Match?':<10}")
    print("-" * 120)

    # Mean IRR
    match = abs(calc_beta_mean_irr - reported_beta_mean_irr) < 0.0001
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Beta Mean IRR':<30} | {calc_beta_mean_irr:>19.4%} | {reported_beta_mean_irr:>19.4%} | {status:<10}")
    if not match:
        discrepancies.append(("Beta Mean IRR", calc_beta_mean_irr, reported_beta_mean_irr))

    # Median IRR
    match = abs(calc_beta_median_irr - reported_beta_median_irr) < 0.0001
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Beta Median IRR':<30} | {calc_beta_median_irr:>19.4%} | {reported_beta_median_irr:>19.4%} | {status:<10}")
    if not match:
        discrepancies.append(("Beta Median IRR", calc_beta_median_irr, reported_beta_median_irr))

    # Mean MOIC
    match = abs(calc_beta_mean_moic - reported_beta_mean_moic) < 0.01
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Beta Mean MOIC':<30} | {calc_beta_mean_moic:>18.4f}x | {reported_beta_mean_moic:>18.4f}x | {status:<10}")
    if not match:
        discrepancies.append(("Beta Mean MOIC", calc_beta_mean_moic, reported_beta_mean_moic))

    print()
    print(f"Sample size: {len(all_beta_irrs):,} investments (≥30 days holding period)")
    print()

    # =========================================================================
    # RECONSTRUCTED GROSS STATISTICS
    # =========================================================================
    print("=" * 120)
    print("RECONSTRUCTED GROSS STATISTICS (Alpha × Beta)")
    print("=" * 120)
    print()

    # Calculate directly from results
    recon_irrs = np.array([r.irr for r in reconstructed_gross_results if r.irr is not None])
    recon_moics = np.array([r.moic for r in reconstructed_gross_results if r.moic is not None])

    calc_recon_mean_irr = np.mean(recon_irrs)
    calc_recon_median_irr = np.median(recon_irrs)
    calc_recon_mean_moic = np.mean(recon_moics)
    calc_recon_median_moic = np.median(recon_moics)

    print(f"{'Metric':<30} | {'Calculated (Raw)':<20} | {'Reported (UI)':<20} | {'Match?':<10}")
    print("-" * 120)

    # Mean IRR
    match = abs(calc_recon_mean_irr - reconstructed_gross_summary.mean_irr) < 0.0001
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Reconstructed Mean IRR':<30} | {calc_recon_mean_irr:>19.4%} | {reconstructed_gross_summary.mean_irr:>19.4%} | {status:<10}")
    if not match:
        discrepancies.append(("Reconstructed Mean IRR", calc_recon_mean_irr, reconstructed_gross_summary.mean_irr))

    # Median IRR
    match = abs(calc_recon_median_irr - reconstructed_gross_summary.median_irr) < 0.0001
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Reconstructed Median IRR':<30} | {calc_recon_median_irr:>19.4%} | {reconstructed_gross_summary.median_irr:>19.4%} | {status:<10}")
    if not match:
        discrepancies.append(("Reconstructed Median IRR", calc_recon_median_irr, reconstructed_gross_summary.median_irr))

    # Mean MOIC
    match = abs(calc_recon_mean_moic - reconstructed_gross_summary.mean_moic) < 0.01
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Reconstructed Mean MOIC':<30} | {calc_recon_mean_moic:>18.4f}x | {reconstructed_gross_summary.mean_moic:>18.4f}x | {status:<10}")
    if not match:
        discrepancies.append(("Reconstructed Mean MOIC", calc_recon_mean_moic, reconstructed_gross_summary.mean_moic))

    # Median MOIC
    match = abs(calc_recon_median_moic - reconstructed_gross_summary.median_moic) < 0.01
    status = "✓" if match else "✗ MISMATCH"
    print(f"{'Reconstructed Median MOIC':<30} | {calc_recon_median_moic:>18.4f}x | {reconstructed_gross_summary.median_moic:>18.4f}x | {status:<10}")
    if not match:
        discrepancies.append(("Reconstructed Median MOIC", calc_recon_median_moic, reconstructed_gross_summary.median_moic))

    print()

    # =========================================================================
    # MATHEMATICAL CONSISTENCY CHECK
    # =========================================================================
    print("=" * 120)
    print("MATHEMATICAL CONSISTENCY CHECK")
    print("=" * 120)
    print()
    print("Checking if (1 + Recon IRR) ≈ (1 + Alpha IRR) × (1 + Beta IRR)")
    print()

    expected_recon_irr = (1 + calc_alpha_mean_irr) * (1 + calc_beta_mean_irr) - 1
    simple_product_error = calc_recon_mean_irr - expected_recon_irr

    print(f"Mean Alpha IRR:           {calc_alpha_mean_irr:>8.2%}")
    print(f"Mean Beta IRR:            {calc_beta_mean_irr:>8.2%}")
    print(f"Mean Reconstructed IRR:   {calc_recon_mean_irr:>8.2%}")
    print()
    print(f"Expected from product:    {expected_recon_irr:>8.2%}")
    print(f"Difference:               {simple_product_error:>+8.2%}")
    print()

    if abs(simple_product_error) > 0.05:  # More than 5%
        print("⚠️  LARGE DISCREPANCY DETECTED!")
        print()
        print("   The reconstructed mean IRR differs significantly from what the")
        print("   multiplicative relationship predicts. This could be due to:")
        print()
        print("   1. Early-period sampling bias (all investments start at day 0)")
        print("   2. Holding period heterogeneity (different T amplifies non-linearity)")
        print("   3. Skewness in return distributions")
        print()
        print("   Run the Beta Sampling Diagnostics to investigate further.")
    else:
        print("✓ Reconstructed mean is consistent with multiplicative relationship")

    print()

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("=" * 120)
    print("SUMMARY")
    print("=" * 120)
    print()

    if discrepancies:
        print(f"⚠️  Found {len(discrepancies)} discrepancy(ies) between calculated and reported values:")
        print()
        for metric, calc, reported in discrepancies:
            diff = calc - reported
            print(f"  {metric}:")
            print(f"    Calculated: {calc if isinstance(calc, str) else f'{calc:.4%}' if abs(calc) < 10 else f'{calc:.4f}'}")
            print(f"    Reported:   {reported if isinstance(reported, str) else f'{reported:.4%}' if abs(reported) < 10 else f'{reported:.4f}'}")
            print(f"    Difference: {diff if isinstance(diff, str) else f'{diff:+.4%}' if abs(diff) < 10 else f'{diff:+.4f}'}")
            print()
    else:
        print("✓ No discrepancies found! All reported statistics match calculated values.")
        print()

    if abs(simple_product_error) > 0.05:
        print("However, there is a large discrepancy in the multiplicative relationship.")
        print("This is NOT a reporting bug - it's a systematic issue with how returns aggregate.")
        print()
        print("Recommendation: Run Beta Sampling Diagnostics to identify the root cause.")
    else:
        print("The multiplicative relationship also checks out.")
        print("Statistics are being calculated and reported correctly.")

    print()
    print("=" * 120)
    print()

    return {
        'discrepancies': discrepancies,
        'alpha_mean_irr_calculated': calc_alpha_mean_irr,
        'alpha_mean_irr_reported': alpha_summary.mean_irr,
        'beta_mean_irr_calculated': calc_beta_mean_irr,
        'beta_mean_irr_reported': reported_beta_mean_irr,
        'recon_mean_irr_calculated': calc_recon_mean_irr,
        'recon_mean_irr_reported': reconstructed_gross_summary.mean_irr,
        'expected_from_product': expected_recon_irr,
        'product_error': simple_product_error
    }


if __name__ == "__main__":
    print("This is a diagnostic module. Import and call diagnose_statistics_reporting()")
    print("from your main application after running deconstructed simulation.")
    print()
    print("Example usage:")
    print("  from diagnose_reporting import diagnose_statistics_reporting")
    print("  diagnostics = diagnose_statistics_reporting(")
    print("      st.session_state.alpha_results,")
    print("      st.session_state.alpha_summary,")
    print("      st.session_state.reconstructed_gross_results,")
    print("      st.session_state.reconstructed_gross_summary,")
    print("      st.session_state.beta_recon_diagnostics")
    print("  )")
