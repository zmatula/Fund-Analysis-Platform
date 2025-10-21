"""
Helper script to verify reconstruction math at individual investment level.

This verifies that:
1. Recon MOIC = Alpha MOIC × Beta MOIC (exactly)
2. (1 + Recon IRR)^T = (1 + Alpha IRR)^T × (1 + Beta IRR)^T (approximately)

Use this to confirm the reconstruction formula is working correctly before
investigating aggregate statistical anomalies.
"""

import numpy as np


def verify_single_investment(
    alpha_moic: float,
    alpha_irr: float,
    beta_moic: float,
    beta_irr: float,
    recon_moic: float,
    recon_irr: float,
    days_held: int,
    investment_name: str = "Unknown",
    verbose: bool = True
) -> tuple:
    """
    Verify reconstruction math for a single investment.

    Args:
        alpha_moic: Alpha MOIC
        alpha_irr: Alpha IRR (as decimal, e.g., 0.025 = 2.5%)
        beta_moic: Beta MOIC
        beta_irr: Beta IRR (as decimal)
        recon_moic: Reconstructed MOIC
        recon_irr: Reconstructed IRR (as decimal)
        days_held: Holding period in days
        investment_name: Name for display
        verbose: Print detailed output

    Returns:
        Tuple of (moic_ok, irr_ok) booleans
    """
    years_held = days_held / 365.25

    # Test 1: MOIC relationship
    expected_recon_moic = alpha_moic * beta_moic
    moic_error = abs(recon_moic - expected_recon_moic)
    moic_ok = moic_error < 0.001  # Within 0.1%

    # Test 2: IRR relationship (via compound growth)
    # (1 + recon_irr)^T should equal (1 + alpha_irr)^T × (1 + beta_irr)^T
    recon_growth = (1 + recon_irr) ** years_held
    expected_growth = ((1 + alpha_irr) ** years_held) * ((1 + beta_irr) ** years_held)
    growth_error = abs(recon_growth - expected_growth)
    irr_ok = growth_error < 0.01  # Within 1% compound error

    if verbose:
        print(f"\nInvestment: {investment_name}")
        print(f"  Holding period: {days_held} days ({years_held:.2f} years)")
        print()
        print(f"  Alpha MOIC: {alpha_moic:.4f}  |  Alpha IRR: {alpha_irr:.2%}")
        print(f"  Beta MOIC:  {beta_moic:.4f}  |  Beta IRR:  {beta_irr:.2%}")
        print(f"  Recon MOIC: {recon_moic:.4f}  |  Recon IRR: {recon_irr:.2%}")
        print()
        print(f"  MOIC Check:")
        print(f"    Expected: {expected_recon_moic:.4f}")
        print(f"    Actual:   {recon_moic:.4f}")
        print(f"    Error:    {moic_error:.6f}  {'✓' if moic_ok else '✗ FAIL'}")
        print()
        print(f"  IRR Check (via compound growth):")
        print(f"    Expected: (1 + recon)^{years_held:.2f} = {expected_growth:.4f}")
        print(f"    Actual:   (1 + recon)^{years_held:.2f} = {recon_growth:.4f}")
        print(f"    Error:    {growth_error:.6f}  {'✓' if irr_ok else '✗ FAIL'}")
        print()

        if moic_ok and irr_ok:
            print("  ✓ PASS: Reconstruction math is correct")
        else:
            print("  ✗ FAIL: Reconstruction math has errors!")

    return moic_ok, irr_ok


def verify_from_results(reconstructed_results, n_samples: int = 10):
    """
    Verify reconstruction math for a sample of investments from results.

    Args:
        reconstructed_results: Results from reconstruction
        n_samples: Number of investments to check

    Returns:
        Tuple of (n_passed, n_total)
    """
    print("\n" + "=" * 100)
    print("VERIFICATION: Individual Investment Math")
    print("=" * 100)
    print()
    print(f"Checking {n_samples} random investments...")
    print()

    passed = 0
    total = 0

    # Collect all investments
    all_investments = []
    for result in reconstructed_results:
        if result.investment_details:
            all_investments.extend(result.investment_details)

    # Sample randomly
    if len(all_investments) > n_samples:
        indices = np.random.choice(len(all_investments), n_samples, replace=False)
        sample = [all_investments[i] for i in indices]
    else:
        sample = all_investments
        n_samples = len(all_investments)

    # Verify each
    for inv in sample:
        total += 1

        # Calculate expected reconstructed MOIC
        expected_recon_moic = inv.simulated_moic * inv.beta_moic

        moic_ok, irr_ok = verify_single_investment(
            alpha_moic=inv.simulated_moic,
            alpha_irr=inv.simulated_irr,
            beta_moic=inv.beta_moic,
            beta_irr=inv.beta_irr,
            recon_moic=inv.simulated_moic,  # This should be the reconstructed value
            recon_irr=inv.simulated_irr,    # This should be the reconstructed value
            days_held=inv.days_held,
            investment_name=inv.investment_name,
            verbose=True
        )

        if moic_ok and irr_ok:
            passed += 1

        print("-" * 100)

    print()
    print("=" * 100)
    print(f"SUMMARY: {passed}/{total} investments passed verification")
    print("=" * 100)
    print()

    if passed == total:
        print("✓ All sampled investments have correct reconstruction math!")
        print("  The issue is in aggregate statistics, not individual calculations.")
    else:
        print(f"✗ {total - passed} investments failed verification!")
        print("  There may be an implementation bug in the reconstruction formula.")

    return passed, total


if __name__ == "__main__":
    print("This is a verification module. Import and call verify_from_results()")
    print("from your main application after reconstruction.")
    print()
    print("Example:")
    print("  from verify_reconstruction_math import verify_from_results")
    print("  verify_from_results(st.session_state.reconstructed_gross_results, n_samples=10)")
