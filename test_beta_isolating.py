"""
Isolating tests to identify where bias is introduced in beta simulation.

Three tests:
A. Drift-only: r_t = mu_fwd_daily (no residuals, no bridge)
B. Drift + Bootstrap: r_t = mu_fwd_daily + eps_boot (no bridge disaggregation)
C. Full: r_t = mu_fwd_daily + eps_boot/N_F + bridge (current implementation)

Expected: All should produce annual arithmetic mean ≈ R_target_blended
"""

import sys
sys.path.insert(0, 'fund_simulation')

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fund_simulation.beta_simulation import (
    circular_block_bootstrap,
    brownian_bridge_increments,
    calibrate_drift_mgf
)

# Configuration matching main simulation
R_view = 0.136  # 13.6% target
R_hist_arith = 0.136  # Assume same for simplicity
w = 0.5
R_target_blended = (1 - w) * R_hist_arith + w * R_view
print(f"R_target_blended = {R_target_blended:.4f} ({R_target_blended*100:.2f}%)")

# Historical parameters (from debug output)
sigma_view = 0.15  # 15% annual vol
sigma_view_daily = sigma_view / np.sqrt(252)
print(f"sigma_view_daily = {sigma_view_daily:.6f}")

# Simulation parameters
n_paths = 1000
horizon_days = 2520  # 10 years
days_per_year = 252
N_F = 21  # Daily disaggregation frequency
K = horizon_days // N_F  # Number of periods
L = 10  # Block length

# Create synthetic residuals (using normal for simplicity)
rng = np.random.default_rng(seed=42)
n_hist_periods = 100
residuals = rng.normal(0, sigma_view_daily * np.sqrt(N_F), n_hist_periods)
residuals = residuals - residuals.mean()

print(f"\nResiduals: mean={residuals.mean():.6f}, std={residuals.std():.6f}")

# Calibrate drift using MGF
print("\n=== Calibrating drift using MGF ===")
vol_scale = 1.0
mu_fwd_daily = calibrate_drift_mgf(
    residuals=residuals,
    R_target=R_target_blended,
    sigma_view=sigma_view,
    N_F=N_F,
    K=K,
    L=L,
    horizon_days=horizon_days,
    sigma_view_daily=sigma_view_daily,
    vol_scale=vol_scale,
    n_pilot=500,
    rng=rng
)

print(f"Calibrated drift: mu_fwd_daily = {mu_fwd_daily:.8f}")
print(f"Annual drift = {mu_fwd_daily * days_per_year:.4f} ({mu_fwd_daily * days_per_year * 100:.2f}%)")

# Calculate period residual std for bridge variance budget
period_residual_std = sigma_view_daily / np.sqrt(N_F)


def measure_annual_arithmetic_mean(paths: np.ndarray, horizon_days: int) -> float:
    """Measure annual arithmetic mean across all non-overlapping years."""
    n_paths = paths.shape[1]
    n_years = horizon_days // days_per_year
    annual_returns = []

    for path_idx in range(n_paths):
        for year in range(n_years):
            start_idx = year * days_per_year
            end_idx = (year + 1) * days_per_year
            price_start = paths[start_idx, path_idx]
            price_end = paths[end_idx, path_idx]
            annual_return = (price_end / price_start) - 1.0
            annual_returns.append(annual_return)

    return np.mean(annual_returns)


def run_test_a_drift_only(n_paths: int, horizon_days: int, mu_fwd_daily: float, rng: np.random.Generator):
    """Test A: Drift only (no residuals, no bridge)"""
    print("\n" + "="*80)
    print("TEST A: DRIFT ONLY")
    print("="*80)
    print("r_t = mu_fwd_daily")
    print(f"Expected annual arithmetic mean ~= {R_target_blended:.4f} ({R_target_blended*100:.2f}%)")

    paths = np.zeros((horizon_days + 1, n_paths))
    paths[0, :] = 100.0  # Initial price

    for path_idx in range(n_paths):
        for t in range(horizon_days):
            # Drift only
            r_t = mu_fwd_daily
            paths[t + 1, path_idx] = paths[t, path_idx] * np.exp(r_t)

    actual = measure_annual_arithmetic_mean(paths, horizon_days)
    print(f"Actual annual arithmetic mean = {actual:.4f} ({actual*100:.2f}%)")
    print(f"Difference = {(actual - R_target_blended)*100:.2f}%")

    return actual


def run_test_b_drift_plus_bootstrap(n_paths: int, horizon_days: int, mu_fwd_daily: float,
                                     residuals: np.ndarray, K: int, L: int, N_F: int,
                                     vol_scale: float, rng: np.random.Generator):
    """Test B: Drift + Bootstrap (no bridge disaggregation)"""
    print("\n" + "="*80)
    print("TEST B: DRIFT + BOOTSTRAP")
    print("="*80)
    print("r_t = mu_fwd_daily + (eps_boot / N_F)")
    print("No bridge disaggregation - just spread period residual evenly")
    print(f"Expected annual arithmetic mean ~= {R_target_blended:.4f} ({R_target_blended*100:.2f}%)")

    paths = np.zeros((horizon_days + 1, n_paths))
    paths[0, :] = 100.0

    for path_idx in range(n_paths):
        # Bootstrap residuals for this path
        eps_boot = circular_block_bootstrap(residuals, K, L, rng)
        eps_boot = vol_scale * eps_boot  # Scale first
        eps_boot = eps_boot - eps_boot.mean()  # Then recenter

        # Build path
        t = 0
        for k in range(K):
            eps_star = eps_boot[k]
            # Spread period residual evenly over N_F days (no bridge)
            for _ in range(N_F):
                if t >= horizon_days:
                    break
                r_t = mu_fwd_daily + (eps_star / N_F)
                paths[t + 1, path_idx] = paths[t, path_idx] * np.exp(r_t)
                t += 1
            if t >= horizon_days:
                break

    actual = measure_annual_arithmetic_mean(paths, horizon_days)
    print(f"Actual annual arithmetic mean = {actual:.4f} ({actual*100:.2f}%)")
    print(f"Difference = {(actual - R_target_blended)*100:.2f}%")

    return actual


def run_test_c_full(n_paths: int, horizon_days: int, mu_fwd_daily: float,
                    residuals: np.ndarray, K: int, L: int, N_F: int,
                    sigma_view_daily: float, period_residual_std: float,
                    vol_scale: float, rng: np.random.Generator):
    """Test C: Full implementation (drift + bootstrap + bridge)"""
    print("\n" + "="*80)
    print("TEST C: FULL (DRIFT + BOOTSTRAP + BRIDGE)")
    print("="*80)
    print("r_t = mu_fwd_daily + (eps_boot / N_F) + bridge_increment")
    print(f"Expected annual arithmetic mean ~= {R_target_blended:.4f} ({R_target_blended*100:.2f}%)")

    paths = np.zeros((horizon_days + 1, n_paths))
    paths[0, :] = 100.0

    for path_idx in range(n_paths):
        # Bootstrap residuals for this path
        eps_boot = circular_block_bootstrap(residuals, K, L, rng)
        eps_boot = vol_scale * eps_boot  # Scale first
        eps_boot = eps_boot - eps_boot.mean()  # Then recenter

        # Build path
        t = 0
        for k in range(K):
            eps_star = eps_boot[k]
            # Generate bridge increments
            daily_inc = brownian_bridge_increments(N_F, sigma_view_daily, period_residual_std, rng)

            # Combine: drift + period residual + bridge
            for i in range(N_F):
                if t >= horizon_days:
                    break
                r_t = mu_fwd_daily + (eps_star / N_F) + daily_inc[i]
                paths[t + 1, path_idx] = paths[t, path_idx] * np.exp(r_t)
                t += 1
            if t >= horizon_days:
                break

    actual = measure_annual_arithmetic_mean(paths, horizon_days)
    print(f"Actual annual arithmetic mean = {actual:.4f} ({actual*100:.2f}%)")
    print(f"Difference = {(actual - R_target_blended)*100:.2f}%")

    return actual


# Run all three tests
print("\n" + "="*80)
print("RUNNING THREE ISOLATING TESTS")
print("="*80)

result_a = run_test_a_drift_only(n_paths, horizon_days, mu_fwd_daily, rng)
result_b = run_test_b_drift_plus_bootstrap(n_paths, horizon_days, mu_fwd_daily, residuals, K, L, N_F, vol_scale, rng)
result_c = run_test_c_full(n_paths, horizon_days, mu_fwd_daily, residuals, K, L, N_F, sigma_view_daily, period_residual_std, vol_scale, rng)

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Target:          {R_target_blended*100:.2f}%")
print(f"Test A (drift):  {result_a*100:.2f}% (diff: {(result_a - R_target_blended)*100:+.2f}%)")
print(f"Test B (+boot):  {result_b*100:.2f}% (diff: {(result_b - R_target_blended)*100:+.2f}%)")
print(f"Test C (+bridge):{result_c*100:.2f}% (diff: {(result_c - R_target_blended)*100:+.2f}%)")

# Incremental changes
print("\n" + "="*80)
print("INCREMENTAL BIAS INTRODUCED")
print("="*80)
print(f"Drift alone:     {result_a*100:.2f}%")
print(f"Adding bootstrap: {(result_b - result_a)*100:+.2f}%")
print(f"Adding bridge:    {(result_c - result_b)*100:+.2f}%")
print(f"Total bias:       {(result_c - R_target_blended)*100:+.2f}%")
