"""Test that terminal distribution has EXACT target statistics"""

import numpy as np
from fund_simulation.beta_import import parse_beta_csv, create_beta_index
from fund_simulation.beta_simulation import simulate_beta_forward

def test_terminal_distribution(n_paths, horizon_days, seed=42):
    """Test terminal distribution accuracy"""

    # Load beta data
    beta_prices, _, _ = parse_beta_csv("temp_beta_upload.csv")
    beta_index = create_beta_index(beta_prices, "quarterly")

    # Run simulation
    beta_paths, diag = simulate_beta_forward(
        beta_index,
        horizon_days=horizon_days,
        n_paths=n_paths,
        seed=seed,
        outlook="base",
        confidence="medium"
    )

    # Calculate terminal returns
    start_price = beta_index.prices[-1].price
    terminal_prices = beta_paths.iloc[-1, :]
    years = horizon_days / 252
    terminal_returns = (terminal_prices / start_price) ** (1/years) - 1

    # Get targets
    r_target = diag['R_view']
    s_target = diag['sigma_view']

    # Calculate actual statistics
    actual_mean = terminal_returns.mean()
    actual_median = terminal_returns.median()
    actual_std = terminal_returns.std()

    # Calculate errors
    mean_error = abs(actual_mean - r_target)
    median_error = abs(actual_median - r_target)
    std_error = abs(actual_std - s_target)

    return {
        'n_paths': n_paths,
        'horizon_days': horizon_days,
        'r_target': r_target,
        's_target': s_target,
        'actual_mean': actual_mean,
        'actual_median': actual_median,
        'actual_std': actual_std,
        'mean_error': mean_error,
        'median_error': median_error,
        'std_error': std_error,
        'mean_error_pct': mean_error / abs(r_target) * 100,
        'median_error_pct': median_error / abs(r_target) * 100,
        'std_error_pct': std_error / s_target * 100
    }

print("=" * 80)
print("EXACT DISTRIBUTION TESTING")
print("=" * 80)

# Test Case 1: 1,000 paths
print("\nTest Case 1: 1,000 paths, 3,650 days (14.5 years)")
print("-" * 80)
result1 = test_terminal_distribution(n_paths=1000, horizon_days=3650)
print(f"Target:  mean={result1['r_target']:.6%}, stdev={result1['s_target']:.6%}")
print(f"Actual:  mean={result1['actual_mean']:.6%}, median={result1['actual_median']:.6%}, stdev={result1['actual_std']:.6%}")
print(f"Errors:  mean={result1['mean_error']:.8%} ({result1['mean_error_pct']:.4f}%)")
print(f"         median={result1['median_error']:.8%} ({result1['median_error_pct']:.4f}%)")
print(f"         stdev={result1['std_error']:.8%} ({result1['std_error_pct']:.4f}%)")

# Test Case 2: 10,000 paths
print("\nTest Case 2: 10,000 paths, 3,650 days (14.5 years)")
print("-" * 80)
result2 = test_terminal_distribution(n_paths=10000, horizon_days=3650)
print(f"Target:  mean={result2['r_target']:.6%}, stdev={result2['s_target']:.6%}")
print(f"Actual:  mean={result2['actual_mean']:.6%}, median={result2['actual_median']:.6%}, stdev={result2['actual_std']:.6%}")
print(f"Errors:  mean={result2['mean_error']:.8%} ({result2['mean_error_pct']:.4f}%)")
print(f"         median={result2['median_error']:.8%} ({result2['median_error_pct']:.4f}%)")
print(f"         stdev={result2['std_error']:.8%} ({result2['std_error_pct']:.4f}%)")

# Test Case 3: Different horizon
print("\nTest Case 3: 1,000 paths, 2,520 days (10 years)")
print("-" * 80)
result3 = test_terminal_distribution(n_paths=1000, horizon_days=2520)
print(f"Target:  mean={result3['r_target']:.6%}, stdev={result3['s_target']:.6%}")
print(f"Actual:  mean={result3['actual_mean']:.6%}, median={result3['actual_median']:.6%}, stdev={result3['actual_std']:.6%}")
print(f"Errors:  mean={result3['mean_error']:.8%} ({result3['mean_error_pct']:.4f}%)")
print(f"         median={result3['median_error']:.8%} ({result3['median_error_pct']:.4f}%)")
print(f"         stdev={result3['std_error']:.8%} ({result3['std_error_pct']:.4f}%)")

# Pass/Fail criteria: errors should be < 0.0001% (essentially machine precision)
print("\n" + "=" * 80)
print("VALIDATION")
print("=" * 80)

tolerance_absolute = 1e-10  # Machine precision
all_passed = True

for i, result in enumerate([result1, result2, result3], 1):
    passed = (result['mean_error'] < tolerance_absolute and
              result['median_error'] < tolerance_absolute and
              result['std_error'] < tolerance_absolute)
    status = "PASS" if passed else "FAIL"
    print(f"Test Case {i}: {status}")
    if not passed:
        all_passed = False
        print(f"  Mean error: {result['mean_error']:.2e}")
        print(f"  Median error: {result['median_error']:.2e}")
        print(f"  Stdev error: {result['std_error']:.2e}")

print("\n" + "=" * 80)
if all_passed:
    print("OVERALL: PASS - Terminal distributions match targets at machine precision!")
else:
    print("OVERALL: FAIL - Errors exceed machine precision")
print("=" * 80)
