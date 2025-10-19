"""Monte Carlo simulation engine"""

import numpy as np
from typing import List, Callable, Optional, Dict

from .models import Investment, SimulationConfiguration, SimulationResult
from .calculators import calculate_holding_period, calculate_irr, calculate_moic


def run_monte_carlo_simulation(
    investments: List[Investment],
    config: SimulationConfiguration,
    progress_callback: Optional[Callable[[float], None]] = None
) -> List[SimulationResult]:
    """
    Run complete Monte Carlo simulation.

    Args:
        investments: List of historical investments
        config: Simulation configuration
        progress_callback: Optional callback for progress updates

    Returns:
        List of simulation results
    """
    # Initialize random state with fixed seed for reproducibility
    random_state = np.random.RandomState(seed=42)

    results = []

    for i in range(config.simulation_count):
        # Run single simulation
        result = run_single_simulation(
            investments, config, i, random_state
        )
        results.append(result)

        # Report progress every 100 simulations
        if progress_callback and (i + 1) % 100 == 0:
            progress_callback((i + 1) / config.simulation_count)

    return results


def run_single_simulation(
    investments: List[Investment],
    config: SimulationConfiguration,
    simulation_id: int,
    random_state: np.random.RandomState
) -> SimulationResult:
    """
    Run a single Monte Carlo simulation iteration.

    Args:
        investments: Available investment universe
        config: Simulation configuration
        simulation_id: ID for this simulation
        random_state: NumPy random state

    Returns:
        SimulationResult object
    """
    # Step 1: Generate portfolio size
    portfolio_size = generate_portfolio_size(
        config.investment_count_mean,
        config.investment_count_std,
        len(investments),
        random_state
    )

    # Step 2: Select investments WITH REPLACEMENT
    selected_investments = select_investments(
        investments, portfolio_size, random_state
    )

    # Step 3: Build cash flow schedule
    cash_flows: Dict[int, float] = {}
    total_invested = 0.0

    for investment in selected_investments:
        # Calculate holding period
        days_held = calculate_holding_period(investment.moic, investment.irr)

        # Investment amount: $1M per position
        investment_amount = 1_000_000
        total_invested += investment_amount

        # Exit cash flow
        exit_amount = investment_amount * investment.moic

        # Aggregate cash flows by day
        if days_held in cash_flows:
            cash_flows[days_held] += exit_amount
        else:
            cash_flows[days_held] = exit_amount

    # Step 4: Calculate total capital (with leverage)
    leverage_amount = total_invested * config.leverage_rate
    total_capital = total_invested + leverage_amount

    # Step 5: Calculate time period
    max_day = max(cash_flows.keys()) if cash_flows else 365
    years_held = max_day / 365.0

    # Step 6: Calculate gross returns
    total_returned = sum(cash_flows.values())
    gross_profit = total_returned - total_capital

    # Step 7: Calculate financial engineering costs
    leverage_cost = leverage_amount * config.cost_of_capital * years_held
    management_fees = total_capital * config.fee_rate * years_held

    # Step 8: Calculate carry
    hurdle_return = total_capital * (1 + config.hurdle_rate * years_held)
    excess_return = max(0, total_returned - hurdle_return)
    carry_paid = excess_return * config.carry_rate

    # Step 9: Calculate net returns to LPs
    net_returned = total_returned - leverage_cost - management_fees - carry_paid
    net_profit = net_returned - total_invested
    net_moic = calculate_moic(net_returned, total_invested)

    # Step 10: Calculate net IRR
    reduction_factor = (net_returned / total_returned) if total_returned > 0 else 0
    net_cash_flows = {day: cf * reduction_factor for day, cf in cash_flows.items()}
    net_irr = calculate_irr(net_cash_flows, total_invested)

    # Step 11: Create result object
    return SimulationResult(
        simulation_id=simulation_id,
        investments_selected=[inv.investment_name for inv in selected_investments],
        investment_count=len(selected_investments),
        total_invested=total_invested,
        total_returned=net_returned,
        moic=net_moic,
        irr=net_irr,
        gross_profit=gross_profit,
        net_profit=net_profit,
        fees_paid=management_fees,
        carry_paid=carry_paid,
        leverage_cost=leverage_cost
    )


def generate_portfolio_size(
    mean: float,
    std_dev: float,
    max_investments: int,
    random_state: np.random.RandomState
) -> int:
    """
    Generate portfolio size from normal distribution.

    Args:
        mean: Mean number of investments
        std_dev: Standard deviation
        max_investments: Maximum possible value
        random_state: NumPy random state

    Returns:
        Integer portfolio size bounded [1, 2 × max_investments]
    """
    # Sample from normal distribution
    size = random_state.normal(loc=mean, scale=std_dev)

    # Round to nearest integer
    size = round(size)

    # Apply bounds
    size = max(1, size)
    size = min(size, max_investments * 2)

    return size


def select_investments(
    investments: List[Investment],
    count: int,
    random_state: np.random.RandomState
) -> List[Investment]:
    """
    Randomly select investments WITH REPLACEMENT.

    Args:
        investments: Available investment universe
        count: Number of investments to select
        random_state: NumPy random state

    Returns:
        List of selected investments (may contain duplicates)
    """
    indices = random_state.choice(len(investments), size=count, replace=True)
    return [investments[i] for i in indices]
