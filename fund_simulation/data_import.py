"""CSV data import and validation"""

import csv
from datetime import datetime
from typing import List, Tuple
from dateutil import parser as date_parser

from .models import Investment


def parse_csv_file(file_path: str) -> Tuple[List[Investment], List[str]]:
    """
    Parse CSV file and return list of Investment objects.

    CSV Format (NO headers):
    investment_name, fund_name, entry_date, latest_date, MOIC, IRR

    Args:
        file_path: Path to CSV file

    Returns:
        Tuple of (investments, errors)
    """
    investments = []
    errors = []
    seen_combinations = set()

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)

        for row_num, row in enumerate(reader, start=1):
            # Skip empty rows
            if not row or all(cell.strip() == '' for cell in row):
                continue

            # Validate column count
            if len(row) != 6:
                errors.append(
                    f"Row {row_num}: Expected 6 columns, found {len(row)}"
                )
                continue

            try:
                # Parse fields
                investment_name = row[0].strip()
                fund_name = row[1].strip()
                entry_date_str = row[2].strip()
                latest_date_str = row[3].strip()
                moic_str = row[4].strip()
                irr_str = row[5].strip()

                # Validate non-empty
                if not investment_name:
                    errors.append(f"Row {row_num}: Investment name is required")
                    continue

                if not fund_name:
                    errors.append(f"Row {row_num}: Fund name is required")
                    continue

                # Parse dates
                try:
                    entry_date = date_parser.parse(entry_date_str)
                except Exception as e:
                    errors.append(
                        f"Row {row_num}: Invalid entry date '{entry_date_str}'"
                    )
                    continue

                try:
                    latest_date = date_parser.parse(latest_date_str)
                except Exception as e:
                    errors.append(
                        f"Row {row_num}: Invalid latest date '{latest_date_str}'"
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

    return investments, errors
