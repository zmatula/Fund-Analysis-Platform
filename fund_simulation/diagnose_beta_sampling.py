"""
Diagnostic tool to analyze beta sampling patterns in reconstruction.

This script helps identify whether the inflated reconstructed IRR (26.25% vs expected 16.44%)
is due to systematic oversampling of the early high-growth period of beta paths.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple
import matplotlib.pyplot as plt


def analyze_beta_temporal_bias(
    reconstructed_results,
    beta_paths: pd.DataFrame,
    beta_start_date
) -> dict:
    """
    Analyze whether beta sampling shows temporal bias.

    Since ALL investments sample from day 0 of beta paths, this checks if:
    1. Different holding periods get different beta returns
    2. Early periods have higher returns than later periods
    3. This explains the inflated aggregate mean

    Args:
        reconstructed_results: Results from reconstruction
        beta_paths: The simulated beta paths (dates × paths)
        beta_start_date: Start date of beta simulation

    Returns:
        Dict with diagnostic information
    """

    print("\n" + "=" * 100)
    print("BETA TEMPORAL SAMPLING BIAS ANALYSIS")
    print("=" * 100)
    print()

    # Extract all investment-level beta returns and holding periods
    all_beta_irrs = []
    all_holding_days = []
    all_alpha_irrs = []
    all_recon_irrs = []

    for result in reconstructed_results:
        if result.investment_details:
            for inv in result.investment_details:
                if inv.beta_irr is not None and inv.days_held >= 30 and inv.alpha_irr is not None:
                    all_beta_irrs.append(inv.beta_irr)
                    all_holding_days.append(inv.days_held)
                    all_alpha_irrs.append(inv.alpha_irr)       # Fixed: use alpha_irr field
                    all_recon_irrs.append(inv.simulated_irr)   # Correct: reconstructed IRR

    all_beta_irrs = np.array(all_beta_irrs)
    all_holding_days = np.array(all_holding_days)
    all_alpha_irrs = np.array(all_alpha_irrs)
    all_recon_irrs = np.array(all_recon_irrs)

    # Summary statistics
    print("OVERALL STATISTICS")
    print("-" * 100)
    print(f"Total investments analyzed: {len(all_beta_irrs):,}")
    print(f"Mean alpha IRR: {np.mean(all_alpha_irrs):.2%}")
    print(f"Mean beta IRR: {np.mean(all_beta_irrs):.2%}")
    print(f"Mean reconstructed IRR: {np.mean(all_recon_irrs):.2%}")
    print()

    # Holding period distribution
    print("HOLDING PERIOD DISTRIBUTION")
    print("-" * 100)
    holding_years = all_holding_days / 365.25
    print(f"Mean: {holding_years.mean():.2f} years")
    print(f"Median: {np.median(holding_years):.2f} years")
    print(f"5th-95th percentile: {np.percentile(holding_years, 5):.2f} - {np.percentile(holding_years, 95):.2f} years")
    print()

    # Bin by holding period and show beta IRR by bin
    print("BETA IRR BY HOLDING PERIOD")
    print("-" * 100)
    bins = [0, 365, 730, 1095, 1460, 1825, 2555, 3650, 10000]
    bin_labels = ['0-1y', '1-2y', '2-3y', '3-4y', '4-5y', '5-7y', '7-10y', '10y+']

    print(f"{'Period':<10} | {'Count':>8} | {'Mean β IRR':>12} | {'Mean α IRR':>12} | {'Mean Recon IRR':>15} | {'Implied Product':>15}")
    print("-" * 100)

    for i, label in enumerate(bin_labels):
        mask = (all_holding_days >= bins[i]) & (all_holding_days < bins[i+1])
        if mask.sum() > 0:
            mean_beta = all_beta_irrs[mask].mean()
            mean_alpha = all_alpha_irrs[mask].mean()
            mean_recon = all_recon_irrs[mask].mean()

            # Calculate what the product formula predicts
            implied_recon = (1 + mean_alpha) * (1 + mean_beta) - 1

            print(f"{label:<10} | {mask.sum():>8,} | {mean_beta:>11.2%} | {mean_alpha:>11.2%} | {mean_recon:>14.2%} | {implied_recon:>14.2%}")

    print()

    # Calculate beta returns for different entry windows of the simulation
    print("BETA PATH ANALYSIS: Returns by Start Year")
    print("-" * 100)
    print("Testing what beta returns look like starting from different years of the simulation")
    print()

    # Sample 100 random paths for analysis
    sample_paths = beta_paths.sample(n=min(100, len(beta_paths.columns)), axis=1)

    # Calculate returns for different holding periods starting from different entry years
    start_years = [0, 1, 2, 3, 4, 5, 7]
    holding_periods_years = [1, 2, 3, 4, 5]

    print(f"{'Start Year':<12} | ", end='')
    for hp in holding_periods_years:
        print(f"  {hp}y Hold  | ", end='')
    print()
    print("-" * 100)

    for start_year in start_years:
        start_day = int(start_year * 365.25)
        if start_day >= len(beta_paths):
            break

        print(f"Year {start_year:<7} | ", end='')

        for hold_years in holding_periods_years:
            hold_days = int(hold_years * 365.25)
            end_day = start_day + hold_days

            if end_day < len(beta_paths):
                # Calculate return from start_day to end_day
                start_prices = sample_paths.iloc[start_day].values
                end_prices = sample_paths.iloc[end_day].values

                moics = end_prices / start_prices
                irrs = (moics ** (1 / hold_years)) - 1
                mean_irr = irrs.mean()

                print(f"{mean_irr:>11.2%} | ", end='')
            else:
                print(f"{'N/A':>11} | ", end='')

        print()

    print()
    print("=" * 100)
    print()

    # Key insight
    print("KEY INSIGHTS:")
    print("-" * 100)

    # Check if early years have systematically higher returns
    year_0_returns = []
    year_5_returns = []
    year_0_avg = None
    year_5_avg = None

    for hold_years in [3, 4, 5]:
        hold_days = int(hold_years * 365.25)

        # Year 0 start
        if hold_days < len(beta_paths):
            start_prices = sample_paths.iloc[0].values
            end_prices = sample_paths.iloc[hold_days].values
            moics = end_prices / start_prices
            irrs = (moics ** (1 / hold_years)) - 1
            year_0_returns.append(irrs.mean())

        # Year 5 start
        start_day = int(5 * 365.25)
        end_day = start_day + hold_days
        if end_day < len(beta_paths):
            start_prices = sample_paths.iloc[start_day].values
            end_prices = sample_paths.iloc[end_day].values
            moics = end_prices / start_prices
            irrs = (moics ** (1 / hold_years)) - 1
            year_5_returns.append(irrs.mean())

    if year_0_returns and year_5_returns:
        year_0_avg = np.mean(year_0_returns)
        year_5_avg = np.mean(year_5_returns)
        difference = year_0_avg - year_5_avg

        print(f"1. Average beta IRR for 3-5 year holds starting at Year 0: {year_0_avg:.2%}")
        print(f"2. Average beta IRR for 3-5 year holds starting at Year 5: {year_5_avg:.2%}")
        print(f"3. Difference: {difference:+.2%}")
        print()

        if difference > 0.02:  # More than 2% difference
            print("⚠️  SIGNIFICANT EARLY-PERIOD BIAS DETECTED!")
            print()
            print("   The beta paths show systematically higher returns in the early years")
            print("   compared to later years. Since ALL investments sample from day 0,")
            print("   they are all capturing this early high-growth period.")
            print()
            print(f"   Current setup: Mean beta IRR = {np.mean(all_beta_irrs):.2%}")
            print(f"   If entry points were randomized: Likely ~{year_5_avg:.2%}")
            print(f"   This explains ~{(np.mean(all_beta_irrs) - year_5_avg):.2%} of the inflation")
        else:
            print("✓  No significant early-period bias detected")
            print("   The inflated returns may be due to other factors")

    print()
    print("=" * 100)

    return {
        'mean_beta_irr': np.mean(all_beta_irrs),
        'mean_alpha_irr': np.mean(all_alpha_irrs),
        'mean_recon_irr': np.mean(all_recon_irrs),
        'mean_holding_years': holding_years.mean(),
        'year_0_avg': year_0_avg if year_0_returns else None,
        'year_5_avg': year_5_avg if year_5_returns else None
    }


def calculate_expected_reconstructed_irr(
    mean_alpha_irr: float,
    mean_beta_irr: float,
    mean_holding_years: float
) -> Tuple[float, float]:
    """
    Calculate what the expected reconstructed IRR should be.

    Two methods:
    1. Simple product: (1 + alpha) × (1 + beta) - 1
    2. MOIC-based: Convert to MOICs, multiply, convert back

    Args:
        mean_alpha_irr: Mean alpha IRR from simulation
        mean_beta_irr: Mean beta IRR from simulation
        mean_holding_years: Mean holding period

    Returns:
        Tuple of (simple_expected, moic_expected)
    """

    # Method 1: Simple product of mean IRRs
    simple_expected = (1 + mean_alpha_irr) * (1 + mean_beta_irr) - 1

    # Method 2: Convert to MOICs, multiply, convert back
    alpha_moic = (1 + mean_alpha_irr) ** mean_holding_years
    beta_moic = (1 + mean_beta_irr) ** mean_holding_years
    recon_moic = alpha_moic * beta_moic
    moic_expected = recon_moic ** (1 / mean_holding_years) - 1

    return simple_expected, moic_expected


if __name__ == "__main__":
    print("This is a diagnostic module. Import and call analyze_beta_temporal_bias()")
    print("from your main application after running reconstruction.")
    print()
    print("Example usage:")
    print("  from diagnose_beta_sampling import analyze_beta_temporal_bias")
    print("  diagnostics = analyze_beta_temporal_bias(")
    print("      st.session_state.reconstructed_gross_results,")
    print("      st.session_state.beta_paths,")
    print("      st.session_state.beta_paths.index[0]")
    print("  )")
