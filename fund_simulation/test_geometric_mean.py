"""Test script to verify geometric mean fix"""

import numpy as np
from fund_simulation.beta_import import parse_beta_csv, create_beta_index
from fund_simulation.beta_simulation import calculate_historical_statistics, simulate_beta_forward

# Load beta data
beta_prices, beta_errors, detected_freq = parse_beta_csv("temp_beta_upload.csv")
beta_index = create_beta_index(beta_prices, "quarterly")

# Calculate historical statistics
hist_stats = calculate_historical_statistics(beta_index)

print("=" * 80)
print("GEOMETRIC MEAN FIX VERIFICATION")
print("=" * 80)

# Manual verification of geometric return
start_price = beta_index.prices[0].price
end_price = beta_index.prices[-1].price
start_date = beta_index.prices[0].date
end_date = beta_index.prices[-1].date
years = (end_date - start_date).days / 365.25

manual_geometric_return = (end_price / start_price) ** (1 / years) - 1

print(f"\nHistorical Data:")
print(f"  Start Date:  {start_date.date()}")
print(f"  End Date:    {end_date.date()}")
print(f"  Start Price: {start_price:.4f}")
print(f"  End Price:   {end_price:.4f}")
print(f"  Years:       {years:.2f}")
print(f"  Total MOIC:  {end_price / start_price:.2f}x")

print(f"\nGeometric Return Calculation:")
print(f"  Function Result:     {hist_stats['annual_return']:.4%}")
print(f"  Manual Calculation:  {manual_geometric_return:.4%}")
print(f"  Match: {'YES' if abs(hist_stats['annual_return'] - manual_geometric_return) < 0.0001 else 'NO'}")

print(f"\nHistorical Statistics:")
print(f"  Annual Return:       {hist_stats['annual_return']:.2%}")
print(f"  Annual Volatility:   {hist_stats['annual_volatility']:.2%}")
print(f"  Observations:        {hist_stats['period_count']}")
print(f"  Frequency:           {hist_stats['frequency']}")

# Run beta simulation with base outlook
print("\n" + "=" * 80)
print("BETA FORWARD SIMULATION TEST (Base Outlook)")
print("=" * 80)

beta_paths, beta_diagnostics = simulate_beta_forward(
    beta_index,
    horizon_days=3650,  # 10 years
    n_paths=1000,
    seed=42,
    outlook="base",
    confidence="medium"
)

# Calculate terminal returns
start_price_sim = beta_index.prices[-1].price
terminal_prices = beta_paths.iloc[-1, :]
years_simulated = 3650 / 252  # Convert trading days to years
terminal_returns = (terminal_prices / start_price_sim) ** (1/years_simulated) - 1  # Annualized

print(f"\nTerminal Return Statistics ({years_simulated:.1f}-year simulation):")
print(f"  Mean Terminal Return:       {terminal_returns.mean():.4%}")
print(f"  Median Terminal Return:     {terminal_returns.median():.4%}")
print(f"  Historical Return (Target): {hist_stats['annual_return']:.4%}")

mean_diff = abs(terminal_returns.mean() - hist_stats['annual_return'])
median_diff = abs(terminal_returns.median() - hist_stats['annual_return'])

print(f"\nAccuracy Check:")
print(f"  Mean vs Historical:   {mean_diff:.4%} {'PASS' if mean_diff < 0.01 else 'FAIL (>1% error)'}")
print(f"  Median vs Historical: {median_diff:.4%} {'PASS' if median_diff < 0.01 else 'FAIL (>1% error)'}")

print(f"\nPercentile Distribution:")
print(f"  5th:    {terminal_returns.quantile(0.05):.2%}")
print(f"  25th:   {terminal_returns.quantile(0.25):.2%}")
print(f"  50th:   {terminal_returns.quantile(0.50):.2%}")
print(f"  75th:   {terminal_returns.quantile(0.75):.2%}")
print(f"  95th:   {terminal_returns.quantile(0.95):.2%}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
