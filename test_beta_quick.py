"""
Quick systematic test - uses 100 paths instead of 1000 for faster results (~5 min total)
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'fund_simulation'))

from fund_simulation.beta_simulation import simulate_beta_forward
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
        n_paths=100,  # Reduced from 1000 for speed
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
print("QUICK SYSTEMATIC BIAS TEST")
print("=" * 80)
print("Testing 5 different seeds with 100 paths each (fast!)")
print()

beta_index = load_beta_data('Lead Edge Beta.csv')
print(f"Loaded {len(beta_index.prices)} price points\n")

results = []
for i, seed in enumerate([42, 43, 44, 45, 46], 1):
    print(f"Run {i}/5 (seed={seed})... ", end='', flush=True)
    result = run_test(beta_index, seed)
    results.append(result)
    print(f"Error: {result['error_pct']:+.2f}%")

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

if all_negative:
    print(f"⚠️  SYSTEMATIC NEGATIVE BIAS - all 5 runs are negative")
    print(f"   This is NOT random noise.")
    print()
    print("RECOMMENDATION: Implement bootstrap sample centering fix")
elif all_positive:
    print(f"⚠️  SYSTEMATIC POSITIVE BIAS - all 5 runs are positive")
elif std_error < 0.05:
    print(f"⚠️  Very low variation (std={std_error:.3f}%) suggests systematic bias")
else:
    print(f"✅ Errors scatter - this appears to be random noise")

print()
