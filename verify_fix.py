"""
Quick verification that the fix is working in production beta_simulation.py
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'fund_simulation'))

# Import from MAIN production file
from fund_simulation.beta_simulation import simulate_beta_forward
from fund_simulation.models import BetaPrice, BetaPriceIndex


def load_beta_data(filepath):
    df = pd.read_csv(filepath, header=None, names=['date', 'price'])
    df['date'] = pd.to_datetime(df['date'], format='%d-%b-%y')
    df = df.sort_values('date')

    beta_prices = [
        BetaPrice(date=row['date'].to_pydatetime(), price=row['price'])
        for _, row in df.iterrows()
    ]

    return BetaPriceIndex(prices=beta_prices, frequency='quarterly')


print("=" * 80)
print("VERIFICATION: Production beta_simulation.py with fix")
print("=" * 80)
print()

beta_index = load_beta_data('Lead Edge Beta.csv')

# Run single test
print("Running simulation (seed=42, 1000 paths, 10 years)...")
paths_df, diagnostics = simulate_beta_forward(
    beta_index=beta_index,
    horizon_days=2520,
    n_paths=1000,
    seed=42,
    outlook='base',
    market_mood='normal',
    confidence='medium'
)

target = diagnostics['R_target_actual']
actual = diagnostics['validation_mean_return']
error = diagnostics['validation_error']

print()
print("=" * 80)
print("RESULT")
print("=" * 80)
print(f"Target:  {target*100:.2f}%")
print(f"Actual:  {actual*100:.2f}%")
print(f"Error:   {error*100:+.2f}%")
print()

if abs(error) < 0.0015:  # 0.15%
    print("SUCCESS! Error < 0.15% - fix is working correctly!")
else:
    print(f"WARNING: Error {error*100:.2f}% is larger than expected")
