"""CSV data import and validation"""

import csv
from datetime import datetime, timedelta
from typing import List, Tuple
from dateutil import parser as date_parser

from .models import Investment, BetaPriceIndex
from .calculators import calculate_holding_period


def parse_csv_file(file_path: str, as_of_date: datetime = None) -> Tuple[List[Investment], List[str]]:
    """
    Parse CSV file and return list of Investment objects.

    CSV Format (NO headers):
    investment_name, fund_name, entry_date, MOIC, IRR

    The exit date (latest_date) is calculated from entry_date + days_held,
    where days_held = 365 * ln(MOIC) / ln(1 + IRR)

    Special case: Investments with MOIC = 1.0 and IRR = 0.0 will have their
    exit date set to the latest exit date among all other investments.

    Args:
        file_path: Path to CSV file
        as_of_date: Date when MOIC/IRR were calculated (optional, defaults to today)

    Returns:
        Tuple of (investments, errors)
    """
    investments = []
    errors = []
    seen_combinations = set()

    # Default as_of_date to today if not provided
    if as_of_date is None:
        as_of_date = datetime.now()

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)

        for row_num, row in enumerate(reader, start=1):
            # Skip empty rows
            if not row or all(cell.strip() == '' for cell in row):
                continue

            # Validate column count (now 5 instead of 6)
            if len(row) != 5:
                errors.append(
                    f"Row {row_num}: Expected 5 columns, found {len(row)}"
                )
                continue

            try:
                # Parse fields
                investment_name = row[0].strip()
                fund_name = row[1].strip()
                entry_date_str = row[2].strip()
                moic_str = row[3].strip()
                irr_str = row[4].strip()

                # Validate non-empty
                if not investment_name:
                    errors.append(f"Row {row_num}: Investment name is required")
                    continue

                if not fund_name:
                    errors.append(f"Row {row_num}: Fund name is required")
                    continue

                # Parse entry date
                try:
                    entry_date = date_parser.parse(entry_date_str)
                except Exception as e:
                    errors.append(
                        f"Row {row_num}: Invalid entry date '{entry_date_str}'"
                    )
                    continue

                # Parse MOIC
                try:
                    moic = float(moic_str)
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid MOIC '{moic_str}'")
                    continue

                # Parse IRR
                try:
                    irr = float(irr_str)
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid IRR '{irr_str}'")
                    continue

                # Adjust IRR = -1.0 edge case
                if irr == -1.0:
                    irr = -0.9999

                # Calculate days held using formula: days = 365 * ln(MOIC) / ln(1 + IRR)
                days_held = calculate_holding_period(moic, irr)

                # Calculate exit date (latest_date) from entry_date + days_held
                latest_date = entry_date + timedelta(days=days_held)

                # Create Investment object
                investment = Investment(
                    investment_name=investment_name,
                    fund_name=fund_name,
                    entry_date=entry_date,
                    latest_date=latest_date,
                    moic=moic,
                    irr=irr
                )

                # Validate
                validation_errors = investment.validate()
                if validation_errors:
                    for err in validation_errors:
                        errors.append(f"Row {row_num}: {err}")
                    continue

                # Check for duplicates
                combo = (investment_name, fund_name)
                if combo in seen_combinations:
                    errors.append(
                        f"Row {row_num}: Duplicate investment '{investment_name}' "
                        f"in fund '{fund_name}'"
                    )
                    # Still add it, but warn
                seen_combinations.add(combo)

                investments.append(investment)

            except Exception as e:
                errors.append(f"Row {row_num}: Unexpected error: {str(e)}")
                continue

    # Second pass: Handle special case for MOIC=1.0, IRR=0.0
    if investments:
        # Find the maximum exit date among investments that are NOT 1.0x/0% break-even
        non_breakeven_dates = [
            inv.latest_date
            for inv in investments
            if not (inv.moic == 1.0 and inv.irr == 0.0)
        ]

        if non_breakeven_dates:
            max_exit_date = max(non_breakeven_dates)

            # Update any break-even investments to use this max date
            for inv in investments:
                if inv.moic == 1.0 and inv.irr == 0.0:
                    inv.latest_date = max_exit_date

    return investments, errors


def decompose_historical_beta(
    investments: List[Investment],
    beta_index: BetaPriceIndex,
    beta_exposure: float = 1.0,
    verbose: bool = True
) -> Tuple[List[Investment], dict]:
    """
    Strip historical beta from investments, returning alpha-only returns.

    Uses multiplicative decomposition:
    - G_total = Total gross return (from MOIC)
    - G_mkt = Market return over same period from beta index
    - G_beta = G_mkt^beta_exposure
    - G_alpha = G_total / G_beta

    Args:
        investments: List of historical investments with total returns
        beta_index: Beta pricing index for historical beta calculation
        beta_exposure: Beta coefficient (default 1.0)
        verbose: Print diagnostic information

    Returns:
        Tuple of:
        - List of Investment objects with alpha-only MOIC/IRR (beta stripped)
        - Dict with decomposition diagnostics
    """
    alpha_investments = []
    skipped_count = 0
    decomposition_details = []

    # Removed verbose output - keeping only Aug 2032 check

    for inv in investments:
        try:
            # Calculate historical market return over holding period
            beta_moic_hist, beta_irr_hist = beta_index.calculate_return(
                inv.entry_date,
                inv.latest_date
            )

            # Total gross return
            G_total = inv.moic

            # Beta component: G_beta = (G_mkt)^beta_exposure
            G_beta = beta_moic_hist ** beta_exposure

            # Alpha component (beta-stripped): G_alpha = G_total / G_beta
            G_alpha = G_total / G_beta

            # Calculate holding period in years
            days_held = (inv.latest_date - inv.entry_date).days
            years_held = days_held / 365.25

            # Alpha IRR: (G_alpha)^(1/T) - 1
            alpha_irr = (G_alpha ** (1 / years_held)) - 1 if years_held > 0 else 0.0

            # Create alpha-only investment
            alpha_inv = Investment(
                investment_name=inv.investment_name,
                fund_name=inv.fund_name,
                entry_date=inv.entry_date,
                latest_date=inv.latest_date,
                moic=G_alpha,  # Alpha MOIC
                irr=alpha_irr   # Alpha IRR
            )

            alpha_investments.append(alpha_inv)

            # Track for diagnostics
            decomposition_details.append({
                'name': inv.investment_name,
                'total_moic': G_total,
                'total_irr': inv.irr,
                'beta_moic': G_beta,
                'beta_irr': beta_irr_hist if beta_exposure == 1.0 else (G_beta ** (1/years_held)) - 1,
                'alpha_moic': G_alpha,
                'alpha_irr': alpha_irr,
                'years_held': years_held
            })

        except ValueError as e:
            # Investment dates outside beta index coverage
            skipped_count += 1
            if verbose and skipped_count <= 5:
                print(f"WARNING: Skipping '{inv.investment_name}' - {str(e)}")
                if skipped_count == 5 and len(investments) > 5:
                    print(f"... (suppressing further warnings)")

    # Calculate summary statistics
    if decomposition_details:
        import numpy as np

        total_irrs = [d['total_irr'] for d in decomposition_details]
        beta_irrs = [d['beta_irr'] for d in decomposition_details]
        alpha_irrs = [d['alpha_irr'] for d in decomposition_details]

        # Create lookup dictionary for reconstruction
        original_returns_lookup = {d['name']: {'moic': d['total_moic'], 'irr': d['total_irr']}
                                   for d in decomposition_details}

        diagnostics = {
            'total_investments': len(investments),
            'decomposed_investments': len(alpha_investments),
            'skipped_investments': skipped_count,
            'mean_total_irr': np.mean(total_irrs),
            'mean_beta_irr': np.mean(beta_irrs),
            'mean_alpha_irr': np.mean(alpha_irrs),
            'details': decomposition_details[:10],  # First 10 for display
            'original_returns_lookup': original_returns_lookup  # All investments for reconstruction
        }

        # Removed verbose summary output
    else:
        diagnostics = {
            'total_investments': len(investments),
            'decomposed_investments': 0,
            'skipped_investments': skipped_count,
            'mean_total_irr': 0.0,
            'mean_beta_irr': 0.0,
            'mean_alpha_irr': 0.0,
            'details': []
        }
        if verbose:
            print(f"ERROR: Could not decompose any investments. All {skipped_count} were outside beta coverage.")

    return alpha_investments, diagnostics
