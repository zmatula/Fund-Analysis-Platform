"""
Test the FIXED version with bootstrap sample centering
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'fund_simulation'))

# Import the FIXED version
from fund_simulation.beta_simulation_test_fixed import simulate_beta_forward
from fund_simulation.models import BetaPrice, BetaPriceIndex


def load_beta_data(filepath):
    """Load beta price data from CSV and create BetaPriceIndex"""
    df = pd.read_csv(filepath, header=None, names=['date', 'price'])
    df['date'] = pd.to_datetime(df['date'], format='%d-%b-%y')
    df = df.sort_values('date')

    beta_prices = [
        BetaPrice(date=row['date'].to_pydatetime(), price=row['price'])
        for _, row in df.iterrows()
    ]

    return BetaPriceIndex(prices=beta_prices, frequency='quarterly')


def run_test(beta_index, seed):
    """Run single test with reduced paths for speed"""
    paths_df, diagnostics = simulate_beta_forward(
        beta_index=beta_index,
        horizon_days=2520,
        n_paths=1000,  # Full sample size for proper testing
        seed=seed,
        outlook='base',
        market_mood='normal',
        confidence='medium'
    )

    return {
        'seed': seed,
        'target': diagnostics['R_target_actual'],
        'actual': diagnostics['validation_mean_return'],
        'error_pct': diagnostics['validation_error'] * 100
    }


print("=" * 80)
print("TESTING FIXED VERSION (with bootstrap sample centering)")
print("=" * 80)
print("Running 5 tests with 1000 paths each to verify the fix works")
print()

beta_index = load_beta_data('Lead Edge Beta.csv')
print(f"Loaded {len(beta_index.prices)} price points\n")

results = []
for i, seed in enumerate([42, 43, 44, 45, 46], 1):
    print(f"Run {i}/5 (seed={seed})... ")
    result = run_test(beta_index, seed)
    results.append(result)
    print(f"  Error: {result['error_pct']:+.2f}%")
    print()

print("=" * 80)
print("RESULTS")
print("=" * 80)

errors = [r['error_pct'] for r in results]
mean_error = np.mean(errors)
std_error = np.std(errors)
all_negative = all(e < 0 for e in errors)
all_positive = all(e > 0 for e in errors)

print(f"Mean error: {mean_error:+.3f}%")
print(f"Std error:  {std_error:.3f}%")
print(f"Min error:  {np.min(errors):+.3f}%")
print(f"Max error:  {np.max(errors):+.3f}%")
print()

if abs(mean_error) < 0.10:
    print("SUCCESS! Mean error < 0.10% - bias is eliminated!")
elif all_negative or all_positive:
    print(f"WARNING: Still systematic bias ({' negative' if all_negative else 'positive'})")
else:
    print("Errors scatter - mostly random noise")

print()
