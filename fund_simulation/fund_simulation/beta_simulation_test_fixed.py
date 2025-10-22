"""Beta forward simulation using circular block bootstrap with daily disaggregation"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional

from .models import BetaPriceIndex


def calibrate_drift_mgf(
    residuals: np.ndarray,
    R_target: float,
    sigma_view: float,
    N_F: int,
    K: int,
    L: int,
    horizon_days: int,
    sigma_view_daily: float,
    vol_scale: float,
    n_pilot: int,
    rng: np.random.Generator
) -> float:
    """
    Calibrate drift using MGF (moment generating function) approach.

    Fix 1: Empirically calibrate drift to hit target arithmetic return
    under the actual (non-Gaussian) bootstrap simulator.

    Args:
        residuals: Historical residuals
        R_target: Target annual arithmetic return
        sigma_view: Target annual volatility
        N_F: Trading days per period
        K: Number of periods needed
        L: Block length for bootstrap
        horizon_days: Simulation horizon in days
        sigma_view_daily: Target daily volatility
        vol_scale: Volatility scaling factor
        n_pilot: Number of pilot paths
        rng: Random generator

    Returns:
        Calibrated daily drift mu_d*
    """
    # Step 1: Run pilot with mu_d = 0
    annual_log_returns = []
    days_per_year = 252

    # Calculate period residual std for bridge variance budget
    # period_residual_std = std(eps_star / N_F) ≈ sigma_view_daily / sqrt(N_F)
    period_residual_std = sigma_view_daily / np.sqrt(N_F)

    # Track eps_boot means before any recentering (for diagnostics)
    eps_boot_means = []

    for i in range(n_pilot):
        # Bootstrap residuals (now using concatenation, not means)
        eps_boot = circular_block_bootstrap(residuals, K, L, rng)

        # Track mean before centering (for diagnostics)
        eps_boot_means.append(eps_boot.mean())

        # FIX: Center the bootstrap SAMPLE (not global path recentering)
        # This eliminates systematic bias from finite sampling
        eps_boot = eps_boot - eps_boot.mean()

        # Scale volatility
        eps_boot = vol_scale * eps_boot

        # Generate period returns with ZERO drift
        r_star = eps_boot

        # Disaggregate to daily returns
        daily_returns = []
        for k in range(K):
            # With mu_d=0, period residual is just r_star[k]
            eps_star = r_star[k]

            # Brownian bridge with variance budget adjustment
            daily_inc = brownian_bridge_increments(N_F, sigma_view_daily, period_residual_std, rng)

            # Daily returns (no drift)
            period_daily = eps_star / N_F + daily_inc
            daily_returns.extend(period_daily)

            if len(daily_returns) >= horizon_days:
                break

        daily_returns = daily_returns[:horizon_days]

        # Calculate annual log returns for ALL complete years (not just first year)
        # This matches the validation metric which averages across all years
        n_years = len(daily_returns) // days_per_year
        for year in range(n_years):
            start_idx = year * days_per_year
            end_idx = (year + 1) * days_per_year
            annual_sum = sum(daily_returns[start_idx:end_idx])
            annual_log_returns.append(annual_sum)

    # Step 2: Compute L = log(mean(exp(S_i)))
    exp_returns = np.exp(annual_log_returns)
    mean_exp = np.mean(exp_returns)
    L = np.log(mean_exp)

    # Step 3: Set mu_d* = (log(1+R_target) - L) / 252
    mu_d_star = (np.log(1 + R_target) - L) / days_per_year

    # Calculate additional diagnostics
    from scipy.stats import skew as scipy_skew
    pilot_skew = scipy_skew(annual_log_returns) if len(annual_log_returns) > 2 else 0.0
    residual_skew = scipy_skew(residuals) if len(residuals) > 2 else 0.0

    # Diagnostic logging
    print(f"\n=== MGF Calibration Diagnostics ===")
    print(f"Target arithmetic return: {R_target:.4f} ({R_target*100:.2f}%)")
    print(f"Pilot paths: {n_pilot}")
    print(f"Pilot annual observations: {len(annual_log_returns)} ({n_pilot} paths × {len(annual_log_returns)//n_pilot if n_pilot > 0 else 0} years)")
    print(f"Annual log returns (zero-drift): mean={np.mean(annual_log_returns):.6f}, std={np.std(annual_log_returns):.6f}")
    print(f"Mean(exp(annual_sum)): {mean_exp:.6f}")
    print(f"L = log(mean(exp(S))): {L:.6f}")
    print(f"log(1+R_target): {np.log(1 + R_target):.6f}")
    print(f"Calibrated mu_daily: {mu_d_star:.8f}")
    print(f"Expected annual return from drift alone: {(np.exp(252 * mu_d_star) - 1)*100:.2f}%")
    print(f"\n--- Additional Diagnostics ---")
    print(f"Skew of annual_log_returns (pilots): {pilot_skew:.6f}")
    print(f"Skew of historical residuals: {residual_skew:.6f}")
    print(f"eps_boot means (before scaling): mean={np.mean(eps_boot_means):.6f}, std={np.std(eps_boot_means):.6f}")
    print(f"===================================\n")

    return mu_d_star


def simulate_beta_forward(
    beta_index: BetaPriceIndex,
    horizon_days: int,
    n_paths: int,
    seed: int = 42,
    outlook: str = "base",
    market_mood: str = "normal",
    confidence: str = "medium",
    annual_return_override: Optional[float] = None,
    vol_target_override: Optional[float] = None
) -> Tuple[pd.DataFrame, Dict]:
    """
    Generate forward price paths using circular block bootstrap with daily disaggregation.

    Args:
        beta_index: Historical beta price index
        horizon_days: Simulation horizon in trading days
        n_paths: Number of Monte Carlo paths
        seed: Random seed for reproducibility
        outlook: "pessimistic", "base", or "optimistic" (user-friendly return view)
        market_mood: "calm", "normal", or "turbulent" (user-friendly vol view)
        confidence: "low", "medium", or "high" (blend weight for user views)
        annual_return_override: Optional direct annual return view (overrides outlook)
        vol_target_override: Optional direct vol target (overrides market_mood)

    Returns:
        Tuple of:
        - DataFrame with shape (horizon_days+1, n_paths), indexed by dates
        - Dict with fitted parameters and diagnostics
    """
    # Set random seed
    np.random.seed(seed)
    rng = np.random.default_rng(seed)

    # Step 1: Preprocess prices to time series
    prices_series, dates = preprocess_prices(beta_index)

    # Step 2: Infer frequency
    freq, N_F = infer_frequency(dates)

    # Step 3: Calculate coarse log returns at detected frequency
    r_F = np.log(prices_series / prices_series.shift(1)).dropna()

    # Check minimum sample size
    if len(r_F) < 36:
        print(f"Warning: Only {len(r_F)} observations at {freq} frequency. Recommend 36+ for stable estimates.")

    # Step 4: Calculate historical moments
    mu_F = r_F.mean()
    sigma_F = r_F.std()
    mu_hist_daily = mu_F / N_F
    sigma_hist_annual = sigma_F * np.sqrt(252 / N_F)

    # Handle edge case: zero volatility
    if sigma_hist_annual < 1e-8:
        print("Warning: Historical volatility near zero. Setting vol scale to 1.0")
        sigma_hist_annual = 0.01  # Minimal fallback

    # Step 5: Map user views
    mu_hist_annual = mu_hist_daily * 252

    # Map outlook to annual return view
    if annual_return_override is not None:
        R_view = annual_return_override
    else:
        outlook_map = {
            "pessimistic": mu_hist_annual - 0.10,
            "base": mu_hist_annual,
            "optimistic": mu_hist_annual + 0.10
        }
        R_view = outlook_map.get(outlook, mu_hist_annual)

    # Map market_mood to vol target
    if vol_target_override is not None:
        sigma_view = vol_target_override
    else:
        mood_map = {
            "calm": 0.12,
            "normal": 0.18,
            "turbulent": 0.28
        }
        sigma_view = mood_map.get(market_mood, 0.18)

    # Map confidence to blend weight
    confidence_map = {
        "low": 0.25,
        "medium": 0.50,
        "high": 0.75
    }
    w = confidence_map.get(confidence, 0.50)

    # Step 6: Prepare vol parameters
    sigma_view_daily = sigma_view / np.sqrt(252)
    vol_scale = sigma_view / sigma_hist_annual

    # Step 7: Block bootstrap parameters
    block_len_map = {
        "daily": 20,
        "monthly": 6,
        "quarterly": 4,
        "annual": 2
    }
    L = block_len_map.get(freq, 6)

    # Adjust block length if insufficient data
    if len(r_F) < 36:
        L = max(2, min(L, len(r_F) // 6))

    # Step 8: Prepare residuals for bootstrap
    residuals = (r_F - mu_F).values

    # Step 9: Determine number of coarse periods needed
    K = int(np.ceil(horizon_days / N_F))

    # Step 10: Generate future dates (trading days)
    last_date = dates[-1]
    future_dates = pd.DatetimeIndex([
        last_date + timedelta(days=i)
        for i in range(horizon_days + 1)
    ])

    # Fix 1: MGF-based drift calibration
    # CRITICAL: Blend in ARITHMETIC space, not mixing log and arithmetic!
    R_hist_arith = np.exp(mu_hist_annual) - 1.0  # Convert log to arithmetic
    R_target_blended = (1 - w) * R_hist_arith + w * R_view  # Both arithmetic now

    # Use sufficient pilot paths to reduce sampling error in L estimation
    # With heavy-tailed distributions (high vol), need large sample to estimate mean(exp(X)) reliably
    n_pilot = n_paths  # Match main simulation sample size for consistent estimates
    mu_fwd_daily = calibrate_drift_mgf(
        residuals=residuals,
        R_target=R_target_blended,  # Use blended target
        sigma_view=sigma_view,
        N_F=N_F,
        K=K,
        L=L,
        horizon_days=horizon_days,
        sigma_view_daily=sigma_view_daily,
        vol_scale=vol_scale,
        n_pilot=n_pilot,
        rng=rng
    )

    # Don't blend again - drift is already calibrated for blended target!
    mu_fwd_period = mu_fwd_daily * N_F

    # Calculate period residual std for bridge variance budget
    period_residual_std = sigma_view_daily / np.sqrt(N_F)

    # Step 11: Simulate paths
    last_price = prices_series.iloc[-1]
    paths = np.zeros((horizon_days + 1, n_paths))
    paths[0, :] = last_price

    for path_idx in range(n_paths):
        # Bootstrap residuals for this path
        eps_boot = circular_block_bootstrap(residuals, K, L, rng)

        # FIX: Center the bootstrap SAMPLE (not global path recentering)
        # This eliminates systematic bias from finite sampling
        eps_boot = eps_boot - eps_boot.mean()

        # Scale volatility
        eps_boot = vol_scale * eps_boot

        # Generate coarse period returns
        r_star = mu_fwd_period + eps_boot

        # Disaggregate to daily returns
        daily_returns = []
        for k in range(K):
            # Period residual after removing mean
            eps_star = r_star[k] - N_F * mu_fwd_daily

            # Brownian bridge with variance budget adjustment
            daily_increments = brownian_bridge_increments(N_F, sigma_view_daily, period_residual_std, rng)

            # Daily returns for this period
            period_daily = mu_fwd_daily + eps_star / N_F + daily_increments

            daily_returns.extend(period_daily)

            # Stop if we've generated enough days
            if len(daily_returns) >= horizon_days:
                break

        # Truncate to exact horizon
        daily_returns = daily_returns[:horizon_days]

        # Build price path
        prices_path = np.zeros(horizon_days + 1)
        prices_path[0] = last_price
        for t in range(horizon_days):
            prices_path[t + 1] = prices_path[t] * np.exp(daily_returns[t])

        paths[:, path_idx] = prices_path

    # Create DataFrame
    paths_df = pd.DataFrame(
        paths,
        index=future_dates,
        columns=[f"Path_{i}" for i in range(n_paths)]
    )

    # Step 12: Calculate confidence intervals
    percentiles = {}
    for q in [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]:
        percentiles[f"P{int(q*100)}"] = np.percentile(paths, q * 100, axis=1)

    # Print simulation configuration
    print(f"\n=== Simulation Configuration ===")
    print(f"Horizon days: {horizon_days}")
    print(f"Frequency: {freq}")
    print(f"Trading days per period (N_F): {N_F}")
    print(f"Block length (L): {L}")
    print(f"Number of historical residuals: {len(residuals)}")
    print(f"Vol scale: {vol_scale:.6f}")
    print(f"================================\n")

    # Validate simulation: measure annual arithmetic mean properly
    # Slice into non-overlapping years across all paths
    days_per_year = 252
    n_years = horizon_days // days_per_year
    annual_returns = []
    annual_returns_by_year = [[] for _ in range(n_years)]

    for path_idx in range(n_paths):
        for year in range(n_years):
            start_idx = year * days_per_year
            end_idx = (year + 1) * days_per_year
            price_start = paths[start_idx, path_idx]
            price_end = paths[end_idx, path_idx]
            annual_return = (price_end / price_start) - 1.0
            annual_returns.append(annual_return)
            annual_returns_by_year[year].append(annual_return)

    actual_mean_return = np.mean(annual_returns) if annual_returns else 0.0
    actual_std_return = np.std(annual_returns) if annual_returns else 0.0

    print(f"\n=== Beta Simulation Validation ===")
    print(f"Target return (blended): {R_target_blended*100:.2f}%")
    print(f"Historical arithmetic: {R_hist_arith*100:.2f}%")
    print(f"User view: {R_view*100:.2f}%")
    print(f"Blend weight (w): {w:.2f}")
    print(f"Calibrated drift: {mu_fwd_daily:.8f} daily")
    print(f"Number of complete years: {n_years}")
    print(f"Total annual observations: {len(annual_returns)} ({n_paths} paths × {n_years} years)")
    print(f"Annual arithmetic mean: {actual_mean_return*100:.2f}%")
    print(f"Annual arithmetic std: {actual_std_return*100:.2f}%")
    print(f"Difference: {(actual_mean_return - R_target_blended)*100:+.2f}%")
    print(f"=====================================\n")

    # Year-by-year analysis
    if n_years > 1:
        print(f"\n=== Year-by-Year Analysis ===")
        for year in range(n_years):
            year_mean = np.mean(annual_returns_by_year[year])
            year_std = np.std(annual_returns_by_year[year])
            print(f"Year {year}: mean={year_mean*100:.2f}%, std={year_std*100:.2f}%")
        print(f"=============================\n")

    # Compile diagnostics
    diagnostics = {
        "frequency": freq,
        "periods_per_year": N_F,
        "n_observations": len(r_F),
        "block_length": L,
        "mu_hist_daily": mu_hist_daily,
        "sigma_hist_annual": sigma_hist_annual,
        "mu_hist_annual": mu_hist_annual,
        "R_view": R_view,
        "R_target_actual": R_target_blended,  # Actual target after blending
        "target_return": R_target_blended,  # Alias for compatibility
        "sigma_view": sigma_view,
        "confidence_weight": w,
        "mu_fwd_daily": mu_fwd_daily,
        "vol_scale": vol_scale,
        "validation_mean_return": actual_mean_return,
        "validation_std_return": actual_std_return,
        "validation_error": actual_mean_return - R_target_blended,
        "last_price": last_price,
        "percentiles": percentiles,
        "outlook": outlook,
        "market_mood": market_mood,
        "confidence": confidence
    }

    return paths_df, diagnostics


def preprocess_prices(beta_index: BetaPriceIndex) -> Tuple[pd.Series, pd.DatetimeIndex]:
    """
    Convert BetaPriceIndex to pandas Series with dates.

    Args:
        beta_index: BetaPriceIndex object

    Returns:
        Tuple of (price series, date index)
    """
    dates = [p.date for p in beta_index.prices]
    prices = [p.price for p in beta_index.prices]

    # Check for non-positive prices
    if any(p <= 0 for p in prices):
        raise ValueError("Beta prices contain non-positive values. Cannot compute log returns.")

    price_series = pd.Series(prices, index=pd.DatetimeIndex(dates))
    price_series = price_series.sort_index()

    return price_series, price_series.index


def infer_frequency(dates: pd.DatetimeIndex) -> Tuple[str, int]:
    """
    Infer data frequency from date gaps.

    Args:
        dates: DatetimeIndex of observations

    Returns:
        Tuple of (frequency_name, trading_days_per_period)
    """
    gaps = np.diff(dates).astype('timedelta64[D]').astype(int)
    median_gap = np.median(gaps)

    if median_gap <= 2:
        return "daily", 1
    elif 20 <= median_gap <= 40:
        return "monthly", 21
    elif 60 <= median_gap <= 100:
        return "quarterly", 63
    elif median_gap >= 300:
        return "annual", 252
    else:
        # Ambiguous - default to monthly
        print(f"Warning: Ambiguous frequency (median gap={median_gap} days). Defaulting to monthly.")
        return "monthly", 21


def circular_block_bootstrap(
    residuals: np.ndarray,
    n_samples: int,
    block_len: int,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Circular block bootstrap of residuals.

    Fix 4: Concatenate blocks instead of taking block means.
    This preserves variance and tail behavior.

    Note: We do NOT recenter blocks (neither per-block nor globally) because:
    - Global recentering creates artificial dependence across the full horizon
    - Per-block recentering can create pathological cancellation when block_len
      matches the measurement period (e.g., if L=4 and years=4 periods, all annual sums=0)
    - Historical residuals already have mean zero; bootstrap preserves this in expectation

    Args:
        residuals: Array of residuals to resample
        n_samples: Number of residual values needed
        block_len: Length of each block
        rng: NumPy random generator

    Returns:
        Bootstrapped residuals array of length n_samples
    """
    n = len(residuals)
    if n == 0:
        raise ValueError("Cannot bootstrap from empty residuals")

    # Create circular array (wrap-around)
    circular = np.concatenate([residuals, residuals])

    # Concatenate blocks until we have enough samples
    sampled = []
    while len(sampled) < n_samples:
        # Random starting point
        start = rng.integers(0, n)
        # Extract block with wrap-around
        block = circular[start:start + block_len]
        sampled.extend(block)

    # Truncate to exact length
    return np.array(sampled[:n_samples])


def brownian_bridge_increments(
    n_steps: int,
    target_daily_vol: float,
    period_residual_std: float,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Generate zero-sum Brownian bridge increments for daily disaggregation.

    The bridge variance is adjusted to account for period residuals already present,
    so total daily variance matches the target.

    Args:
        n_steps: Number of daily steps
        target_daily_vol: Target daily volatility for scaling
        period_residual_std: Std dev of period residual contribution (eps_star/N_F)
        rng: NumPy random generator

    Returns:
        Array of length n_steps with zero sum
    """
    if n_steps == 1:
        return np.array([0.0])

    # Calculate bridge variance budget after accounting for period residuals
    # Total daily var = Var(eps*/N_F) + Var(bridge)
    # So: Var(bridge) = target_var - Var(eps*/N_F)
    target_var = target_daily_vol ** 2
    period_var = period_residual_std ** 2
    bridge_var = max(target_var - period_var, 0.0)  # Ensure non-negative
    bridge_std = np.sqrt(bridge_var)

    # If period residuals already exceed target, use zero bridge
    if bridge_std < 1e-8:
        return np.zeros(n_steps)

    # Generate standard Brownian increments
    z = rng.standard_normal(n_steps)

    # Cumulative sum (Brownian motion)
    W = np.cumsum(z)

    # Brownian bridge: remove linear drift to endpoint
    t = np.arange(1, n_steps + 1)
    B = W - (t / n_steps) * W[-1]

    # Calculate increments
    dB = np.diff(np.concatenate([[0], B]))

    # Enforce EXACT zero sum (numerical safety)
    dB = dB - dB.sum() / n_steps

    # Verify zero sum
    assert abs(dB.sum()) < 1e-10, f"Bridge increments don't sum to zero: {dB.sum()}"

    # Scale to bridge target (NOT total target)
    if dB.std() > 1e-8:
        alpha = bridge_std / dB.std()
    else:
        alpha = 1.0

    # Clip alpha to prevent extreme scaling
    alpha = np.clip(alpha, 0.1, 10.0)

    return alpha * dB
