"""Monte Carlo simulation engine"""

import numpy as np
from typing import List, Callable, Optional, Dict

from .models import Investment, SimulationConfiguration, SimulationResult, BetaPriceIndex, InvestmentDetail
from .calculators import (
    calculate_holding_period,
    calculate_irr,
    calculate_irr_robust,
    calculate_moic,
    calculate_alpha_metrics,
    calculate_beta_return
)


def run_monte_carlo_simulation(
    investments: List[Investment],
    config: SimulationConfiguration,
    progress_callback: Optional[Callable[[float], None]] = None,
    beta_index: Optional[BetaPriceIndex] = None,
    export_details: bool = False,
    apply_costs: bool = True,
    use_alpha: bool = False
) -> List[SimulationResult]:
    """
    Run complete Monte Carlo simulation.

    Args:
        investments: List of historical investments
        config: Simulation configuration
        progress_callback: Optional callback for progress updates
        beta_index: Beta price index for alpha decomposition
        export_details: Whether to track detailed investment data and cash flows
        apply_costs: Whether to apply fees, carry, and leverage to results
        use_alpha: Whether to use alpha (excess) returns instead of absolute returns

    Returns:
        List of simulation results
    """
    # Initialize random state with fixed seed for reproducibility
    random_state = np.random.RandomState(seed=42)

    results = []

    for i in range(config.simulation_count):
        # Run single simulation
        result = run_single_simulation(
            investments, config, i, random_state, beta_index, export_details,
            apply_costs, use_alpha
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
    random_state: np.random.RandomState,
    beta_index: Optional[BetaPriceIndex] = None,
    export_details: bool = False,
    apply_costs: bool = True,
    use_alpha: bool = False
) -> SimulationResult:
    """
    Run a single Monte Carlo simulation iteration.

    Args:
        investments: Available investment universe
        config: Simulation configuration
        simulation_id: ID for this simulation
        random_state: NumPy random state
        beta_index: Beta price index for alpha decomposition
        export_details: Whether to track detailed investment data and cash flows
        apply_costs: Whether to apply fees, carry, and leverage
        use_alpha: Whether to calculate alpha (excess) returns

    Returns:
        SimulationResult object
    """
    # Diagnostic flags
    has_negative_cash_flows = False
    irr_converged = True
    negative_total_returned = False

    # Initialize detail tracking
    investment_details = [] if export_details else None

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
        # Determine which MOIC/IRR to use
        beta_moic_val = None
        beta_irr_val = None

        # CRITICAL FIX: When use_alpha=True, investments ALREADY have alpha values
        # from decompose_historical_beta(). Do NOT recalculate alpha here or we'll
        # strip beta TWICE (double decomposition bug).
        #
        # The beta_index parameter is only for tracking beta metrics in investment_details,
        # not for recalculating alpha.

        if use_alpha and beta_index is not None:
            # Alpha mode: investments already contain alpha values
            # Just calculate beta for tracking/diagnostics purposes
            try:
                # Calculate beta return over investment period (for tracking only)
                beta_moic, beta_irr = calculate_beta_return(
                    beta_index,
                    investment.entry_date,
                    investment.latest_date
                )
                beta_moic_val = beta_moic
                beta_irr_val = beta_irr

            except ValueError:
                # Beta data doesn't cover this investment - skip it
                continue

        # Use investment metrics directly (alpha if use_alpha=True, total if False)
        simulation_moic = investment.moic
        simulation_irr = investment.irr

        # Calculate holding period
        days_held = calculate_holding_period(simulation_moic, simulation_irr)

        # Investment amount: $1M per position
        investment_amount = 1_000_000
        total_invested += investment_amount

        # Exit cash flow (can be negative in alpha mode!)
        exit_amount = investment_amount * simulation_moic

        # Track negative cash flows
        if exit_amount < 0:
            has_negative_cash_flows = True

        # Aggregate cash flows by day
        if days_held in cash_flows:
            cash_flows[days_held] += exit_amount
        else:
            cash_flows[days_held] = exit_amount

        # Track investment details if requested
        if export_details and investment_details is not None:
            from datetime import timedelta
            exit_date = investment.entry_date + timedelta(days=days_held)
            investment_details.append(InvestmentDetail(
                investment_name=investment.investment_name,
                entry_date=investment.entry_date,
                exit_date=exit_date,
                simulated_moic=simulation_moic,
                simulated_irr=simulation_irr,
                beta_moic=beta_moic_val,
                beta_irr=beta_irr_val,
                days_held=days_held,
                investment_amount=investment_amount
            ))

    # Step 4: Calculate time period
    max_day = max(cash_flows.keys()) if cash_flows else 365
    years_held = max_day / 365.25  # Using 365.25 for leap year adjustment

    # Step 5: Calculate returns
    gross_returned = sum(cash_flows.values())

    # Track negative total returns
    if gross_returned < 0:
        negative_total_returned = True

    # Apply or skip costs based on apply_costs parameter
    if not apply_costs:
        # Gross mode: no leverage, fees, or carry
        total_capital = total_invested
        leverage_amount = 0.0
        leverage_cost = 0.0
        management_fees = 0.0
        carry_paid = 0.0

        # Net returns = Gross returns when not applying costs
        net_returned = gross_returned
        gross_profit = gross_returned - total_invested
        net_profit = gross_profit
        net_moic = calculate_moic(net_returned, total_invested)

    else:
        # Net mode: Calculate with leverage, fees, and carry
        leverage_amount = total_invested * config.leverage_rate
        total_capital = total_invested + leverage_amount
        gross_profit = gross_returned - total_capital

        # Financial engineering costs
        leverage_cost = leverage_amount * config.cost_of_capital * years_held
        management_fees = total_capital * config.fee_rate * years_held

        # Calculate carry
        hurdle_return = total_capital * (1 + config.hurdle_rate * years_held)
        excess_return = max(0, gross_returned - hurdle_return)
        carry_paid = excess_return * config.carry_rate

        # Net returns to LPs
        net_returned = gross_returned - leverage_cost - management_fees - carry_paid
        net_profit = net_returned - total_invested
        net_moic = calculate_moic(net_returned, total_invested)

    # Step 10: Calculate net IRR using robust method
    reduction_factor = (net_returned / gross_returned) if gross_returned > 0 else 0
    net_cash_flows = {day: cf * reduction_factor for day, cf in cash_flows.items()}

    # Use robust IRR if using alpha or if we have negative cash flows
    if use_alpha or has_negative_cash_flows:
        net_irr, irr_converged = calculate_irr_robust(net_cash_flows, total_invested)
    else:
        net_irr = calculate_irr(net_cash_flows, total_invested)
        irr_converged = True

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
        leverage_cost=leverage_cost,
        has_negative_cash_flows=has_negative_cash_flows,
        irr_converged=irr_converged,
        negative_total_returned=negative_total_returned,
        investment_details=investment_details,
        cash_flow_schedule=cash_flows if export_details else None
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
