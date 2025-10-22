"""Performance reconstruction for deconstructed simulation mode"""

import numpy as np
import pandas as pd
from typing import List, Dict
from datetime import datetime, timedelta

from .models import SimulationResult, SimulationConfiguration, InvestmentDetail
from .calculators import calculate_moic, calculate_irr, calculate_irr_robust


def reconstruct_gross_performance(
    alpha_results: List[SimulationResult],
    beta_paths: pd.DataFrame,
    beta_start_date: datetime,
    config: SimulationConfiguration,
    random_state: np.random.RandomState,
    original_returns_lookup: Dict[str, Dict[str, float]] = None
) -> List[SimulationResult]:
    """
    Reconstruct gross returns by combining alpha with simulated beta paths.

    For each alpha simulation:
    1. For each investment with alpha_moic and days_held
    2. Select a random beta path
    3. Calculate beta_moic over holding period from path
    4. Reconstruct: total_moic = alpha_moic * (beta_moic ^ β)
    5. Aggregate to portfolio level

    Args:
        alpha_results: List of alpha simulation results
        beta_paths: DataFrame of simulated beta paths (dates × paths)
        beta_start_date: Starting date for beta simulation
        config: Simulation configuration (for beta exposure)
        random_state: NumPy random state for reproducibility

    Returns:
        Tuple of:
        - List of SimulationResult with reconstructed gross returns
        - Dict with beta diagnostics (mean/median/percentiles of actual beta returns used)
    """
    reconstructed_results = []
    n_beta_paths = len(beta_paths.columns)

    # Diagnostics
    total_alpha_investments = 0
    skipped_investments = 0
    beta_horizon_days = (beta_paths.index[-1] - beta_paths.index[0]).days

    # Track actual beta returns used in reconstruction
    all_beta_moics = []
    all_beta_irrs = []

    # Diagnostic: Track investments for detailed output
    investment_counter = 0
    diagnostic_header_printed = False

    for alpha_result in alpha_results:
        # Skip if no investment details tracked
        if alpha_result.investment_details is None:
            continue

        # Reconstruct cash flows for this portfolio
        cash_flows: Dict[int, float] = {}
        total_invested = 0.0

        # Tracking for diagnostics
        has_negative_cash_flows = False
        irr_converged = True
        negative_total_returned = False

        # New investment details with reconstructed returns
        reconstructed_details = []

        for inv_detail in alpha_result.investment_details:
            total_alpha_investments += 1

            # Select a random beta path for this investment
            beta_path_idx = random_state.randint(0, n_beta_paths)
            beta_path_name = beta_paths.columns[beta_path_idx]

            # Calculate beta MOIC over holding period
            try:
                beta_moic = calculate_beta_moic_from_path(
                    beta_paths[beta_path_name],
                    beta_start_date,
                    inv_detail.days_held
                )
            except ValueError as e:
                # If holding period exceeds beta simulation horizon, skip this investment
                skipped_investments += 1
                continue

            # Reconstruct total MOIC using geometric attribution
            # Total MOIC = Alpha MOIC × (Beta MOIC ^ β)
            reconstructed_moic = inv_detail.simulated_moic * (beta_moic ** config.beta_exposure)

            # Reconstruct total IRR
            # Using the formula: (1 + total_irr) = (1 + alpha_irr) × (1 + beta_irr)^β
            if inv_detail.days_held > 0:
                years_held = inv_detail.days_held / 365.25

                # Calculate beta IRR from beta MOIC
                beta_irr = (beta_moic ** (1 / years_held)) - 1

                # Calculate alpha IRR (already stored)
                alpha_irr = inv_detail.simulated_irr

                # Reconstruct total IRR
                reconstructed_irr = ((1 + alpha_irr) * ((1 + beta_irr) ** config.beta_exposure)) - 1

                # Track beta metrics for diagnostics (only if holding period is meaningful)
                # Filter out extremely short holding periods to avoid IRR calculation artifacts
                if inv_detail.days_held >= 30:  # At least 30 days
                    all_beta_moics.append(beta_moic)
                    all_beta_irrs.append(beta_irr)
            else:
                reconstructed_irr = 0.0
                beta_irr = 0.0

            # Verbose diagnostic output removed - keeping only Aug 2032 check

            # Investment amount
            investment_amount = inv_detail.investment_amount
            total_invested += investment_amount

            # Exit cash flow
            exit_amount = investment_amount * reconstructed_moic

            # Track negative cash flows
            if exit_amount < 0:
                has_negative_cash_flows = True

            # Aggregate cash flows by day
            days_held = inv_detail.days_held
            if days_held in cash_flows:
                cash_flows[days_held] += exit_amount
            else:
                cash_flows[days_held] = exit_amount

            # Store reconstructed investment detail
            reconstructed_details.append(InvestmentDetail(
                investment_name=inv_detail.investment_name,
                entry_date=inv_detail.entry_date,
                exit_date=inv_detail.exit_date,
                simulated_moic=reconstructed_moic,
                simulated_irr=reconstructed_irr,
                alpha_moic=inv_detail.simulated_moic,  # Preserve alpha MOIC
                alpha_irr=inv_detail.simulated_irr,    # Preserve alpha IRR
                beta_moic=beta_moic,
                beta_irr=beta_irr if inv_detail.days_held > 0 else 0.0,
                days_held=inv_detail.days_held,
                investment_amount=investment_amount
            ))

        # Calculate portfolio-level returns
        if not cash_flows:
            continue

        max_day = max(cash_flows.keys())
        years_held = max_day / 365.25

        gross_returned = sum(cash_flows.values())

        # Track negative total returns
        if gross_returned < 0:
            negative_total_returned = True

        # Gross mode: no leverage, fees, or carry
        gross_profit = gross_returned - total_invested
        gross_moic = calculate_moic(gross_returned, total_invested)

        # Calculate gross IRR using robust method
        if has_negative_cash_flows:
            gross_irr, irr_converged = calculate_irr_robust(cash_flows, total_invested)
        else:
            gross_irr = calculate_irr(cash_flows, total_invested)
            irr_converged = True

        # Create result object (gross returns, no costs)
        reconstructed_result = SimulationResult(
            simulation_id=alpha_result.simulation_id,
            investments_selected=[d.investment_name for d in reconstructed_details],
            investment_count=len(reconstructed_details),
            total_invested=total_invested,
            total_returned=gross_returned,
            moic=gross_moic,
            irr=gross_irr,
            gross_profit=gross_profit,
            net_profit=gross_profit,  # Same as gross in this stage
            fees_paid=0.0,
            carry_paid=0.0,
            leverage_cost=0.0,
            has_negative_cash_flows=has_negative_cash_flows,
            irr_converged=irr_converged,
            negative_total_returned=negative_total_returned,
            investment_details=reconstructed_details,
            cash_flow_schedule=cash_flows
        )

        reconstructed_results.append(reconstructed_result)

    if len(reconstructed_results) == 0:
        raise ValueError(
            f"Reconstruction produced zero results. All {total_alpha_investments} alpha investments "
            f"exceeded the beta simulation horizon of {beta_horizon_days} days. "
            f"Increase beta_horizon_days to at least the maximum investment holding period."
        )

    # Calculate beta diagnostics
    beta_diagnostics = {}
    if all_beta_irrs:
        beta_irrs_array = np.array(all_beta_irrs)
        beta_moics_array = np.array(all_beta_moics)

        beta_diagnostics = {
            'mean_beta_irr': float(np.mean(beta_irrs_array)),
            'median_beta_irr': float(np.median(beta_irrs_array)),
            'p5_beta_irr': float(np.percentile(beta_irrs_array, 5)),
            'p95_beta_irr': float(np.percentile(beta_irrs_array, 95)),
            'mean_beta_moic': float(np.mean(beta_moics_array)),
            'median_beta_moic': float(np.median(beta_moics_array)),
            'n_investments': len(all_beta_irrs)
        }

    return reconstructed_results, beta_diagnostics


def calculate_beta_moic_from_path(
    beta_path: pd.Series,
    start_date: datetime,
    days_held: int
) -> float:
    """
    Calculate beta MOIC over holding period from a simulated path.

    This function measures beta return from day 0 to day N of the path,
    where N = days_held. The start_date parameter is only used for validation.

    Args:
        beta_path: Series of beta prices indexed by date (forward simulation)
        start_date: Beta simulation start date (first date in beta_path.index)
        days_held: Holding period in days

    Returns:
        Beta MOIC over period

    Raises:
        ValueError: If holding period exceeds path length
    """
    # Validate that beta path starts from the expected start_date
    path_start = beta_path.index[0]

    # Entry price is the first price in the path (time 0)
    entry_price = beta_path.iloc[0]

    # Exit is at days_held from the start
    # The beta path represents forward simulation, so we measure from index 0 forward
    exit_date = path_start + timedelta(days=days_held)

    # Check if exit date is within path
    if exit_date > beta_path.index[-1]:
        raise ValueError(
            f"Holding period {days_held} days exceeds beta simulation horizon. "
            f"Beta path ends at {beta_path.index[-1].date()}, but exit needed at {exit_date.date()}"
        )

    # Find exit price via interpolation
    if exit_date in beta_path.index:
        exit_price = beta_path.loc[exit_date]
    else:
        # Linear interpolation between surrounding dates
        dates_before = beta_path.index[beta_path.index <= exit_date]
        dates_after = beta_path.index[beta_path.index > exit_date]

        if len(dates_before) == 0 or len(dates_after) == 0:
            raise ValueError(f"Cannot interpolate beta price for {exit_date.date()}")

        date_before = dates_before[-1]
        date_after = dates_after[0]

        price_before = beta_path.loc[date_before]
        price_after = beta_path.loc[date_after]

        # Linear interpolation
        days_total = (date_after - date_before).days
        days_from_start = (exit_date - date_before).days

        if days_total == 0:
            exit_price = price_before
        else:
            weight = days_from_start / days_total
            exit_price = price_before + (price_after - price_before) * weight

    # Calculate MOIC
    beta_moic = exit_price / entry_price

    return beta_moic


def reconstruct_net_performance(
    gross_results: List[SimulationResult],
    config: SimulationConfiguration
) -> List[SimulationResult]:
    """
    Apply fees, carry, and leverage to gross results.

    Args:
        gross_results: List of gross simulation results
        config: Simulation configuration with fee/carry/leverage parameters

    Returns:
        List of SimulationResult with net returns after costs
    """
    net_results = []

    for gross_result in gross_results:
        # Extract values
        total_invested = gross_result.total_invested
        gross_returned = gross_result.total_returned
        max_day = max(gross_result.cash_flow_schedule.keys()) if gross_result.cash_flow_schedule else 365
        years_held = max_day / 365.25

        # Apply leverage
        leverage_amount = total_invested * config.leverage_rate
        total_capital = total_invested + leverage_amount

        # Gross profit (relative to total capital including leverage)
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

        # Calculate net IRR using robust method
        if gross_result.cash_flow_schedule:
            reduction_factor = (net_returned / gross_returned) if gross_returned > 0 else 0
            net_cash_flows = {
                day: cf * reduction_factor
                for day, cf in gross_result.cash_flow_schedule.items()
            }

            if gross_result.has_negative_cash_flows:
                net_irr, irr_converged = calculate_irr_robust(net_cash_flows, total_invested)
            else:
                net_irr = calculate_irr(net_cash_flows, total_invested)
                irr_converged = True
        else:
            net_irr = 0.0
            irr_converged = False

        # Create net result
        net_result = SimulationResult(
            simulation_id=gross_result.simulation_id,
            investments_selected=gross_result.investments_selected,
            investment_count=gross_result.investment_count,
            total_invested=total_invested,
            total_returned=net_returned,
            moic=net_moic,
            irr=net_irr,
            gross_profit=gross_profit,
            net_profit=net_profit,
            fees_paid=management_fees,
            carry_paid=carry_paid,
            leverage_cost=leverage_cost,
            has_negative_cash_flows=gross_result.has_negative_cash_flows,
            irr_converged=irr_converged,
            negative_total_returned=gross_result.negative_total_returned,
            investment_details=gross_result.investment_details,
            cash_flow_schedule=gross_result.cash_flow_schedule
        )

        net_results.append(net_result)

    return net_results
