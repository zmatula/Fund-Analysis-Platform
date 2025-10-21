"""Core calculation functions for Monte Carlo simulation"""

import math
from typing import Dict, Tuple
from datetime import datetime


def calculate_holding_period(moic: float, irr: float) -> int:
    """
    Calculate holding period in days from MOIC and IRR.

    Formula: days = 365 × ln(MOIC) / ln(1 + IRR)

    Args:
        moic: Multiple on Invested Capital (must be > 0)
        irr: Internal Rate of Return as decimal (must be > -1.0)

    Returns:
        Number of days (minimum 1)

    Edge Cases:
        - MOIC ≤ 0: Returns 365 (default)
        - IRR = -1.0: Adjusted to -0.9999 to avoid log(0)
        - Calculation failure: Returns 365 (default)
    """
    # Handle edge cases
    if moic <= 0:
        return 365  # Default to 1 year

    if irr == -1.0:
        irr = -0.9999  # Avoid log(0)

    try:
        # Calculate using logarithmic formula
        days = 365 * math.log(moic) / math.log(1 + irr)
        days = round(days)
        days = max(1, days)  # At least 1 day
        return days
    except (ValueError, ZeroDivisionError):
        # If calculation fails, default to 365 days
        return 365


def calculate_irr(
    cash_flows: Dict[int, float],
    initial_investment: float,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> float:
    """
    Calculate IRR using Newton-Raphson method.

    Args:
        cash_flows: Dictionary mapping day → cash flow amount
        initial_investment: Initial investment (positive number)
        max_iterations: Maximum iterations for convergence
        tolerance: Convergence tolerance

    Returns:
        IRR as decimal (e.g., 0.25 for 25%)

    Convergence:
        - Max iterations: 100
        - Tolerance: 1e-6
        - Initial guess: 0.1 (10%)
        - Rate bounds: [-0.9999, 10.0]
    """
    rate = 0.1  # Initial guess (10%)

    for iteration in range(max_iterations):
        # Calculate NPV and derivative
        npv = -initial_investment
        dnpv = 0.0

        for day, cash_flow in cash_flows.items():
            years = day / 365.25  # Using 365.25 for leap year adjustment
            discount_factor = (1 + rate) ** years

            # NPV contribution
            npv += cash_flow / discount_factor

            # Derivative contribution
            dnpv -= years * cash_flow / (discount_factor * (1 + rate))

        # Check convergence
        if abs(npv) < tolerance:
            return rate

        # Avoid division by zero
        if dnpv == 0:
            break

        # Newton-Raphson update
        rate = rate - npv / dnpv

        # Bound the rate to reasonable range
        rate = max(-0.9999, min(rate, 10.0))

    # Return best estimate even if not converged
    return rate


def calculate_moic(total_returned: float, total_invested: float) -> float:
    """
    Calculate Multiple on Invested Capital.

    Args:
        total_returned: Total cash returned
        total_invested: Total cash invested

    Returns:
        MOIC (e.g., 2.5 for 2.5x return)
    """
    if total_invested <= 0:
        return 0.0
    return total_returned / total_invested


def verify_npv(
    rate: float,
    cash_flows: Dict[int, float],
    initial_investment: float
) -> float:
    """
    Calculate NPV for a given rate to verify IRR calculation.

    Args:
        rate: Discount rate to test
        cash_flows: Dictionary mapping day → cash flow amount
        initial_investment: Initial investment (positive number)

    Returns:
        NPV value (should be near 0 if rate is correct IRR)
    """
    npv = -initial_investment

    for day, cash_flow in cash_flows.items():
        years = day / 365.25  # Using 365.25 for leap year adjustment
        discount_factor = (1 + rate) ** years
        npv += cash_flow / discount_factor

    return npv


def calculate_irr_bisection(
    cash_flows: Dict[int, float],
    initial_investment: float,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> float:
    """
    Calculate IRR using bisection method (more robust but slower).

    This method always converges if IRR exists between bounds.

    Args:
        cash_flows: Dictionary mapping day → cash flow amount
        initial_investment: Initial investment (positive number)
        max_iterations: Maximum iterations
        tolerance: Convergence tolerance

    Returns:
        IRR as decimal

    Raises:
        ValueError: If IRR cannot be found in reasonable range
    """
    # Define search bounds
    lower = -0.9999
    upper = 10.0

    # Check if bounds bracket a zero
    npv_lower = verify_npv(lower, cash_flows, initial_investment)
    npv_upper = verify_npv(upper, cash_flows, initial_investment)

    # If both have same sign, no IRR in this range
    if npv_lower * npv_upper > 0:
        # Return boundary based on which is closer to zero
        if abs(npv_lower) < abs(npv_upper):
            return lower
        else:
            return upper

    # Bisection loop
    for _ in range(max_iterations):
        mid = (lower + upper) / 2.0
        npv_mid = verify_npv(mid, cash_flows, initial_investment)

        if abs(npv_mid) < tolerance:
            return mid

        # Narrow the bracket
        if npv_mid * npv_lower < 0:
            upper = mid
            npv_upper = npv_mid
        else:
            lower = mid
            npv_lower = npv_mid

    # Return best estimate
    return (lower + upper) / 2.0


def calculate_irr_robust(
    cash_flows: Dict[int, float],
    initial_investment: float
) -> Tuple[float, bool]:
    """
    Calculate IRR with robust handling of negative cash flows.

    Implements fallback strategy:
    1. Try Newton-Raphson with default initial guess
    2. Try Newton-Raphson with multiple initial guesses
    3. Fall back to bisection method
    4. Return floor value if all fail

    Args:
        cash_flows: Dictionary mapping day → cash flow amount
        initial_investment: Initial investment (positive number)

    Returns:
        Tuple of (irr, converged) where:
        - irr: IRR as decimal
        - converged: True if calculation converged successfully
    """
    # Try Newton-Raphson with default guess
    try:
        rate = calculate_irr(cash_flows, initial_investment)

        # Verify solution (NPV should be near zero)
        npv = verify_npv(rate, cash_flows, initial_investment)
        if abs(npv) < 1000:  # Reasonable tolerance for verification
            return rate, True
    except:
        pass

    # Fallback 1: Try different initial guesses
    for initial_guess in [-0.5, 0.0, 0.5, 1.0, 2.0]:
        try:
            rate = calculate_irr(
                cash_flows,
                initial_investment,
                max_iterations=100,
                tolerance=1e-6
            )

            # Manual Newton-Raphson with custom initial guess
            rate = initial_guess
            for iteration in range(100):
                npv = -initial_investment
                dnpv = 0.0

                for day, cash_flow in cash_flows.items():
                    years = day / 365.25  # Using 365.25 for leap year adjustment
                    discount_factor = (1 + rate) ** years
                    npv += cash_flow / discount_factor
                    dnpv -= years * cash_flow / (discount_factor * (1 + rate))

                if abs(npv) < 1e-6:
                    # Verify this solution
                    if abs(verify_npv(rate, cash_flows, initial_investment)) < 1000:
                        return rate, True
                    break

                if dnpv == 0:
                    break

                rate = rate - npv / dnpv
                rate = max(-0.9999, min(rate, 10.0))

        except:
            continue

    # Fallback 2: Bisection method (slower but more robust)
    try:
        rate = calculate_irr_bisection(cash_flows, initial_investment)
        npv = verify_npv(rate, cash_flows, initial_investment)
        if abs(npv) < 1000:
            return rate, True
    except:
        pass

    # Fallback 3: Return floor value based on total cash flows
    total_cash_flows = sum(cash_flows.values())
    if total_cash_flows < 0:
        # Lost everything
        return -0.9999, False
    elif total_cash_flows < initial_investment * 0.5:
        # Significant loss
        return -0.75, False
    else:
        # Break even or slight gain
        return 0.0, False


def calculate_alpha_metrics(
    investment_moic: float,
    investment_irr: float,
    beta_moic: float,
    beta_irr: float,
    days_held: int,
    beta_exposure: float = 1.0
) -> Tuple[float, float]:
    """
    Calculate alpha using geometric attribution.

    Formulas:
    - t = days_held / 365.25
    - Alpha MOIC = MOIC_p / (MOIC_m ^ β)
    - Alpha IRR = (Alpha MOIC)^(1/t) - 1

    Where:
    - MOIC_p = investment MOIC
    - MOIC_m = beta/index MOIC
    - β = beta exposure (default 1.0)
    - t = time period in years

    Args:
        investment_moic: Investment MOIC (MOIC_p)
        investment_irr: Investment IRR (not used in geometric method)
        beta_moic: Beta benchmark MOIC (MOIC_m)
        beta_irr: Beta benchmark IRR (not used in geometric method)
        days_held: Number of days investment was held
        beta_exposure: Beta exposure coefficient (default 1.0)

    Returns:
        Tuple of (alpha_moic, alpha_irr)

    Note:
        Alpha can be negative (underperformance).
    """
    # Calculate time period in years (using 365.25 for leap year adjustment)
    t = days_held / 365.25

    # Geometric attribution for Alpha MOIC
    # Alpha MOIC = MOIC_p / (MOIC_m ^ β)
    if beta_moic > 0:
        alpha_moic = investment_moic / (beta_moic ** beta_exposure)
    else:
        # Edge case: if beta is negative or zero, can't calculate geometric alpha
        alpha_moic = investment_moic

    # Calculate Alpha IRR from Alpha MOIC
    # Alpha IRR = (Alpha MOIC)^(1/t) - 1
    if t > 0 and alpha_moic > 0:
        alpha_irr = (alpha_moic ** (1 / t)) - 1
    else:
        # Edge case: if time is zero or alpha MOIC is negative
        alpha_irr = 0.0

    return alpha_moic, alpha_irr


def calculate_beta_return(
    beta_index,
    entry_date: datetime,
    exit_date: datetime
) -> Tuple[float, float]:
    """
    Calculate beta benchmark return over an investment period.

    Args:
        beta_index: BetaPriceIndex object with price data
        entry_date: Investment entry date
        exit_date: Investment exit date

    Returns:
        Tuple of (beta_moic, beta_irr)

    Raises:
        ValueError: If dates are outside beta data coverage
    """
    return beta_index.calculate_return(entry_date, exit_date)
