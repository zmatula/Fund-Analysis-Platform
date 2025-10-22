"""Quick verification that the fix works correctly"""

from fund_simulation.beta_import import parse_beta_csv, create_beta_index
from fund_simulation.beta_simulation import simulate_beta_forward
import numpy as np

# Load your data
beta_prices, _, _ = parse_beta_csv('temp_beta_upload.csv')
beta_index = create_beta_index(beta_prices, 'quarterly')

# Run simulation with same settings as app default
beta_paths, diag = simulate_beta_forward(
    beta_index,
    horizon_days=3650,  # ~14.5 years
    n_paths=1000,
    seed=42,
    outlook='base',
    confidence='medium'
)

# Your chart data points
start_date = beta_index.prices[-1].date
start_price = beta_index.prices[-1].price

print("\n" + "=" * 80)
print("VERIFICATION: Chart Median Values")
print("=" * 80)

# Find October 2025 (start + ~1 month)
oct_2025_idx = 20  # Approximately 20 trading days later
oct_2025_median = beta_paths.iloc[oct_2025_idx, :].median()

# Find August 2032 (start + ~6.92 years)
aug_2032_idx = int(6.92 * 252)  # ~1743 trading days
aug_2032_median = beta_paths.iloc[aug_2032_idx, :].median()

# Calculate annualized returns
years_to_aug = aug_2032_idx / 252
ann_return = (aug_2032_median / start_price) ** (1/years_to_aug) - 1

print(f"\nStart (Sept 2025):")
print(f"  Price: {start_price:.2f}")

print(f"\nOctober 2025 (~1 month later):")
print(f"  Median price: {oct_2025_median:.2f}")
print(f"  (You saw: 65.78 in old version)")

print(f"\nAugust 2032 (~6.92 years later):")
print(f"  Median price: {aug_2032_median:.2f}")
print(f"  (You saw: 252.77 in old version)")

print(f"\nAnnualized Return (Sept 2025 to Aug 2032):")
print(f"  Actual: {ann_return:.2%}")
print(f"  Target: {diag['R_view']:.2%}")
print(f"  Difference: {abs(ann_return - diag['R_view']):.4%}")

print(f"\nExpected median in Aug 2032 for 14.57% return:")
expected = start_price * (1.1457 ** years_to_aug)
print(f"  {expected:.2f}")

# Terminal statistics
terminal_prices = beta_paths.iloc[-1, :]
years_total = beta_paths.shape[0] / 252
terminal_returns = (terminal_prices / start_price) ** (1/years_total) - 1

print(f"\nTerminal Statistics (end of simulation):")
print(f"  Mean return: {terminal_returns.mean():.4%}")
print(f"  Median return: {terminal_returns.median():.4%}")
print(f"  Target: {diag['R_view']:.4%}")

if abs(terminal_returns.median() - diag['R_view']) < 0.0001:
    print("\nFIX VERIFIED: Median matches target!")
else:
    print("\nIssue: Median does not match target")

print("=" * 80)
