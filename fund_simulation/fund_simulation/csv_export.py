"""CSV export functions for detailed simulation data"""

import csv
from typing import List, Union, IO
from io import StringIO
from .models import SimulationResult


def export_investment_details(results: List[SimulationResult], output: Union[str, IO, StringIO]) -> int:
    """
    Export detailed investment-level data to CSV file or buffer.

    CSV columns:
    - Simulation Number
    - Investment Name
    - Entry Date
    - Exit Date
    - Days Held
    - Investment Amount
    - Simulated MOIC
    - Simulated IRR
    - Beta MOIC (if alpha mode)
    - Beta IRR (if alpha mode)

    Args:
        results: List of simulation results with investment_details populated
        output: Path to output CSV file OR file-like object/StringIO buffer

    Returns:
        Number of rows written
    """
    rows_written = 0

    # Handle both file paths and buffers
    if isinstance(output, str):
        # It's a file path
        csvfile = open(output, 'w', newline='', encoding='utf-8')
        should_close = True
    else:
        # It's already a file-like object
        csvfile = output
        should_close = False

    try:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow([
            'Simulation Number',
            'Investment Name',
            'Entry Date',
            'Exit Date',
            'Days Held',
            'Investment Amount',
            'Simulated MOIC',
            'Simulated IRR',
            'Beta MOIC',
            'Beta IRR'
        ])

        # Write data
        for result in results:
            if result.investment_details is None:
                continue

            for detail in result.investment_details:
                writer.writerow([
                    result.simulation_id,
                    detail.investment_name,
                    detail.entry_date.strftime('%Y-%m-%d'),
                    detail.exit_date.strftime('%Y-%m-%d'),
                    detail.days_held,
                    f"{detail.investment_amount:.2f}",
                    f"{detail.simulated_moic:.6f}",
                    f"{detail.simulated_irr:.6f}",
                    f"{detail.beta_moic:.6f}" if detail.beta_moic is not None else "",
                    f"{detail.beta_irr:.6f}" if detail.beta_irr is not None else ""
                ])
                rows_written += 1

        return rows_written
    finally:
        if should_close:
            csvfile.close()


def export_cash_flow_schedules(results: List[SimulationResult], output: Union[str, IO, StringIO]) -> int:
    """
    Export cash flow schedules for each simulated fund to CSV file or buffer.

    Each row represents a cash flow event:
    - Simulation Number
    - Day
    - Cash Flow Amount

    Args:
        results: List of simulation results with cash_flow_schedule populated
        output: Path to output CSV file OR file-like object/StringIO buffer

    Returns:
        Number of rows written
    """
    rows_written = 0

    # Handle both file paths and buffers
    if isinstance(output, str):
        # It's a file path
        csvfile = open(output, 'w', newline='', encoding='utf-8')
        should_close = True
    else:
        # It's already a file-like object
        csvfile = output
        should_close = False

    try:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow([
            'Simulation Number',
            'Day',
            'Cash Flow Amount'
        ])

        # Write data
        for result in results:
            if result.cash_flow_schedule is None:
                continue

            # Sort by day for cleaner output
            for day in sorted(result.cash_flow_schedule.keys()):
                cash_flow = result.cash_flow_schedule[day]
                writer.writerow([
                    result.simulation_id,
                    day,
                    f"{cash_flow:.2f}"
                ])
                rows_written += 1

        return rows_written
    finally:
        if should_close:
            csvfile.close()
