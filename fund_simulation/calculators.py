"""Core calculation functions for Monte Carlo simulation"""

import math
from typing import Dict


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
            years = day / 365.0
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
