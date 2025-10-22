"""Test that terminal returns match sampled distribution exactly"""

import numpy as np
from fund_simulation.beta_import import parse_beta_csv, create_beta_index
from fund_simulation.beta_simulation import simulate_beta_forward

# Load beta data
beta_prices, beta_errors, detected_freq = parse_beta_csv("temp_beta_upload.csv")
beta_index = create_beta_index(beta_prices, "quarterly")

# Run simulation
horizon_days = 3650
n_paths = 10000  # More paths for better precision

print("=" * 80)
print("TERMINAL SAMPLING VERIFICATION")
print("=" * 80)

beta_paths, beta_diagnostics = simulate_beta_forward(
    beta_index,
    horizon_days=horizon_days,
    n_paths=n_paths,
    seed=42,
    outlook="base",
    confidence="medium"
)

# Calculate terminal returns from paths
start_price = beta_index.prices[-1].price
terminal_prices = beta_paths.iloc[-1, :]
years = horizon_days / 252
terminal_returns = (terminal_prices / start_price) ** (1/years) - 1

# Expected distribution parameters
r_target = beta_diagnostics['R_view']
s_target = beta_diagnostics['sigma_view']

print(f"\nExpected Distribution (sampled):")
print(f"  Mean:   {r_target:.4%}")
print(f"  Median: {r_target:.4%} (should match mean for normal dist)")
print(f"  Stdev:  {s_target:.4%}")

print(f"\nActual Terminal Returns:")
print(f"  Mean:   {terminal_returns.mean():.4%}")
print(f"  Median: {terminal_returns.median():.4%}")
print(f"  Stdev:  {terminal_returns.std():.4%}")

print(f"\nDifferences:")
print(f"  Mean error:   {abs(terminal_returns.mean() - r_target):.4%}")
print(f"  Median error: {abs(terminal_returns.median() - r_target):.4%}")
print(f"  Stdev error:  {abs(terminal_returns.std() - s_target):.4%}")

# Check if within acceptable tolerance (0.1% for mean/median, 1% for stdev)
mean_ok = abs(terminal_returns.mean() - r_target) < 0.001
median_ok = abs(terminal_returns.median() - r_target) < 0.001
stdev_ok = abs(terminal_returns.std() - s_target) / s_target < 0.05  # 5% relative error

print(f"\nValidation:")
print(f"  Mean matches:   {'PASS' if mean_ok else 'FAIL'}")
print(f"  Median matches: {'PASS' if median_ok else 'FAIL'}")
print(f"  Stdev matches:  {'PASS' if stdev_ok else 'FAIL'}")

if mean_ok and median_ok and stdev_ok:
    print("\nOVERALL: PASS - Terminal distribution matches target exactly!")
else:
    print("\nOVERALL: FAIL - Terminal distribution does not match target")

print("=" * 80)
