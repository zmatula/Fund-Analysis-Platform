"""Beta forward simulation using constant-growth paths"""

# VERSION MARKER - DO NOT REMOVE
__BETA_SIMULATION_VERSION__ = "v2.1_exact_moments_FIXED_TRADING_DAYS_BUG"

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Dict

from .models import BetaPriceIndex


def calculate_historical_statistics(beta_index: BetaPriceIndex) -> dict:
    """
    Calculate annualized mean return and volatility from historical beta data.

    Process:
    1. Calculate geometric annualized return from total price change
    2. Extract all period-to-period returns for volatility calculation
    3. Annualize volatility based on frequency

    Args:
        beta_index: Historical beta price index

    Returns:
        dict with:
            - annual_return: Annualized geometric return
            - annual_volatility: Annualized standard deviation
            - period_count: Number of periods analyzed
            - frequency: Data frequency
            - start_date, end_date: Data range
    """
    prices = beta_index.prices

    # Calculate geometric annualized return from total price change
    start_price = prices[0].price
    end_price = prices[-1].price
    total_return_multiple = end_price / start_price

    # Calculate time period in years
    start_date = prices[0].date
    end_date = prices[-1].date
    years = (end_date - start_date).days / 365.25

    # Geometric annualized return
    annual_return = total_return_multiple ** (1 / years) - 1

    # Calculate period-to-period returns for volatility
    returns = []
    for i in range(1, len(prices)):
        ret = (prices[i].price / prices[i-1].price) - 1
        returns.append(ret)

    returns_array = np.array(returns)
    periodic_std = np.std(returns_array, ddof=1)  # Sample stdev

    # Annualization factor based on frequency
    freq_map = {
        'daily': 252,
        'weekly': 52,
        'monthly': 12,
        'quarterly': 4,
        'annual': 1,
        'irregular': 12  # Default to monthly if irregular
    }

    periods_per_year = freq_map.get(beta_index.frequency, 12)

    # Annualize volatility
    annual_volatility = periodic_std * np.sqrt(periods_per_year)

    return {
        'annual_return': annual_return,
        'annual_volatility': annual_volatility,
        'period_count': len(returns),
        'frequency': beta_index.frequency,
        'start_date': start_date,
        'end_date': end_date
    }


def _draw_norm_with_exact_moments(n_paths: int, mean: float, sigma: float, seed: int) -> np.ndarray:
    """
    Draw from normal distribution with EXACT mean, median, and standard deviation.

    Uses symmetric antithetic pairs to enforce:
    - mean = median = target mean (by construction)
    - standard deviation = target sigma (via exact rescaling)

    Args:
        n_paths: Number of samples to draw
        mean: Target mean and median
        sigma: Target standard deviation
        seed: Random seed for reproducibility

    Returns:
        Array of n_paths samples with exact mean, median, and stdev
    """
    rng = np.random.default_rng(seed)

    # Generate symmetric antithetic pairs → mean=0 and median=0 exactly
    m = n_paths // 2
    a = np.abs(rng.standard_normal(m))  # half-normal magnitudes
    z = np.concatenate([-a, a])  # symmetric pairs

    if n_paths % 2 == 1:
        z = np.concatenate([z, np.array([0.0])])  # exact central 0 → median 0

    rng.shuffle(z)

    # Rescale to unit std exactly (mean already 0 by construction)
    z = z / np.sqrt(np.mean(z**2))

    # Transform to target distribution
    return mean + sigma * z


def simulate_beta_forward(
    beta_index: BetaPriceIndex,
    horizon_days: int,
    n_paths: int,
    seed: int = 42,
    outlook: str = "base",
    confidence: str = "medium"
) -> Tuple[pd.DataFrame, Dict]:
    """
    Simulate beta price paths using constant-growth approach.

    Methodology:
    1. Calculate historical annualized return (r_hist) and volatility (s_hist)
    2. Apply outlook modifier: r_target = r_hist + modifier
       - pessimistic: -10%
       - base: 0%
       - optimistic: +10%
    3. Apply confidence modifier: s_target = s_hist × multiplier
       - low: 1.5× (more uncertainty)
       - medium: 1.0× (historical)
       - high: 0.5× (less uncertainty)
    4. Draw n TERMINAL annualized returns from N(r_target, s_target) with EXACT moments
    5. For each terminal return, calculate the daily rate needed to achieve it
    6. Each path compounds at its constant daily rate for horizon_days

    Args:
        beta_index: Historical beta price index
        horizon_days: Number of trading days to simulate
        n_paths: Number of Monte Carlo paths
        seed: Random seed for reproducibility
        outlook: Return scenario ("pessimistic", "base", "optimistic")
        confidence: Uncertainty level ("low", "medium", "high")

    Returns:
        Tuple of:
        - DataFrame: paths (dates × paths), starting from day 1
        - dict: diagnostics with historical and forward parameters
    """
    # Step 1: Calculate historical statistics
    hist_stats = calculate_historical_statistics(beta_index)
    r_hist = hist_stats['annual_return']
    s_hist = hist_stats['annual_volatility']

    # Step 2: Apply outlook modifier (ADDITIVE)
    outlook_modifiers = {
        "pessimistic": -0.10,
        "base": 0.00,
        "optimistic": 0.10
    }
    r_target = r_hist + outlook_modifiers[outlook]

    # Step 3: Apply confidence modifier to stdev (MULTIPLICATIVE)
    confidence_modifiers = {
        "low": 1.5,      # More uncertainty = wider distribution
        "medium": 1.0,   # Historical volatility
        "high": 0.5      # Less uncertainty = tighter distribution
    }
    s_target = s_hist * confidence_modifiers[confidence]

    # Step 4: Draw n TERMINAL annualized returns with EXACT moments
    # Use symmetric antithetic pairs to ensure exact mean, median, and stdev
    terminal_annual_returns = _draw_norm_with_exact_moments(
        n_paths=n_paths,
        mean=r_target,
        sigma=s_target,
        seed=seed
    )

    # Step 5: Generate constant-growth paths
    start_price = beta_index.prices[-1].price
    start_date = beta_index.prices[-1].date

    # Calculate simulation period in years
    years = horizon_days / 252

    paths = {}

    for i in range(n_paths):
        terminal_return = terminal_annual_returns[i]

        # Calculate total multiple needed to achieve terminal return over simulation period
        total_multiple = (1 + terminal_return) ** years

        # Find constant daily return that achieves this multiple
        daily_return = total_multiple ** (1 / horizon_days) - 1

        # Compound for horizon_days - initialize current_price for each path
        prices = []
        current_price = start_price  # Fresh start for each path

        for day in range(horizon_days):
            current_price = current_price * (1 + daily_return)
            prices.append(current_price)

        paths[f'path_{i}'] = prices

    # CRITICAL: Create DataFrame with dates spanning the correct time period
    #
    # horizon_days represents TRADING DAYS (252 per year), NOT calendar days!
    #
    # WRONG: pd.date_range(freq='D', periods=2520) creates 2520 CALENDAR days (~6.9 years)
    # RIGHT: Convert trading days to calendar time, then create date range
    #
    # For 2520 trading days:
    #   - This represents 10 years of trading (2520 / 252 = 10)
    #   - Must span ~10 calendar years (not 6.9 years)
    #   - End date should be ~2035, not 2032
    #
    # See CRITICAL_TRADING_DAYS_VS_CALENDAR_DAYS.md for full documentation
    calendar_years = horizon_days / 252
    end_date = start_date + timedelta(days=int(calendar_years * 365.25))

    # Create evenly-spaced dates spanning the full period
    dates = pd.date_range(start=start_date + timedelta(days=1), end=end_date, periods=horizon_days)
    paths_df = pd.DataFrame(paths, index=dates)

    # Calculate terminal statistics for diagnostics
    terminal_prices = paths_df.iloc[-1, :]
    terminal_returns = (terminal_prices / start_price) ** (1 / years) - 1

    # Diagnostics
    diagnostics = {
        # Historical
        'frequency': hist_stats['frequency'],
        'n_observations': hist_stats['period_count'],
        'mu_hist_annual': r_hist,
        'sigma_hist_annual': s_hist,
        'mu_hist_daily': (1 + r_hist) ** (1/252) - 1,  # For compatibility

        # Forward parameters
        'outlook': outlook,
        'confidence': confidence,
        'R_view': r_target,
        'sigma_view': s_target,

        # Simulation settings
        'n_paths': n_paths,
        'horizon_days': horizon_days,
        'start_price': start_price,
        'start_date': start_date,

        # Terminal statistics
        'terminal_mean_price': float(terminal_prices.mean()),
        'terminal_median_price': float(terminal_prices.median()),
        'terminal_mean_return': float(terminal_returns.mean()),
        'terminal_median_return': float(terminal_returns.median())
    }

    return paths_df, diagnostics
