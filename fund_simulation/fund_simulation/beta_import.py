"""Beta price data import and frequency detection"""

from datetime import datetime
from typing import List, Tuple, Union, IO
import csv
from dateutil.parser import parse as parse_date
import numpy as np
from io import StringIO

from .models import BetaPrice, BetaPriceIndex


def detect_frequency(dates: List[datetime]) -> str:
    """
    Detect the frequency of beta price data based on gaps between dates.

    Args:
        dates: List of datetime objects (must be sorted)

    Returns:
        One of: "daily", "weekly", "monthly", "quarterly", "annual", "irregular", "insufficient_data"
    """
    if len(dates) < 2:
        return "insufficient_data"

    # Calculate gaps between consecutive dates
    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
    median_gap = np.median(gaps)

    # Classify based on median gap
    if median_gap <= 2:
        return "daily"
    elif 5 <= median_gap <= 9:
        return "weekly"
    elif 25 <= median_gap <= 35:
        return "monthly"
    elif 85 <= median_gap <= 95:
        return "quarterly"
    elif 360 <= median_gap <= 370:
        return "annual"
    else:
        return "irregular"


def parse_beta_csv(file_path_or_buffer: Union[str, IO, StringIO]) -> Tuple[List[BetaPrice], List[str], str]:
    """
    Parse beta price CSV file or buffer and auto-detect frequency.

    Expected CSV format (no headers):
        date,price
        2015-07-01,100.00
        2015-08-01,105.00

    Or with headers:
        date,price
        2015-07-01,100.00

    Args:
        file_path_or_buffer: Path to CSV file OR file-like object/StringIO buffer

    Returns:
        Tuple of (prices_list, errors_list, detected_frequency)
    """
    prices = []
    errors = []

    try:
        # Handle both file paths and buffers
        if isinstance(file_path_or_buffer, str):
            # It's a file path
            f = open(file_path_or_buffer, 'r', encoding='utf-8-sig')
            should_close = True
        else:
            # It's already a file-like object
            f = file_path_or_buffer
            should_close = False

        try:
            reader = csv.reader(f)
            rows = list(reader)

            if not rows:
                errors.append("CSV file is empty")
                return [], errors, "insufficient_data"

            # Check if first row is header
            first_row = rows[0]
            has_header = False
            try:
                # Try to parse first row as data
                _test_date = _parse_date_flexible(first_row[0])
                float(first_row[1])
            except:
                # First row is probably a header
                has_header = True
                rows = rows[1:]

            if not rows:
                errors.append("CSV file has no data rows")
                return [], errors, "insufficient_data"

            # Parse each row
            for row_num, row in enumerate(rows, start=2 if has_header else 1):
                try:
                    if len(row) < 2:
                        errors.append(f"Row {row_num}: Expected 2 columns (date, price), got {len(row)}")
                        continue

                    # Parse date
                    try:
                        date = _parse_date_flexible(row[0])
                    except Exception as e:
                        errors.append(f"Row {row_num}: Could not parse date '{row[0]}': {str(e)}")
                        continue

                    # Parse price
                    try:
                        price = float(row[1])
                    except ValueError:
                        errors.append(f"Row {row_num}: Could not parse price '{row[1]}' as a number")
                        continue

                    # Create BetaPrice object
                    beta_price = BetaPrice(date=date, price=price)

                    # Validate
                    price_errors = beta_price.validate()
                    if price_errors:
                        for err in price_errors:
                            errors.append(f"Row {row_num}: {err}")
                        continue

                    prices.append(beta_price)

                except Exception as e:
                    errors.append(f"Row {row_num}: Unexpected error: {str(e)}")
                    continue

            # Sort prices by date
            prices.sort(key=lambda p: p.date)

            # Detect frequency
            if prices:
                dates = [p.date for p in prices]
                detected_frequency = detect_frequency(dates)
            else:
                detected_frequency = "insufficient_data"

            # Check for duplicate dates
            date_counts = {}
            for i, p in enumerate(prices, start=1):
                date_str = p.date.date().isoformat()
                if date_str in date_counts:
                    errors.append(
                        f"Duplicate date {date_str} found (rows {date_counts[date_str]} and {i})"
                    )
                else:
                    date_counts[date_str] = i

            return prices, errors, detected_frequency
        finally:
            if should_close:
                f.close()

    except FileNotFoundError:
        errors.append(f"File not found: {file_path_or_buffer}")
        return [], errors, "insufficient_data"
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")
        return [], errors, "insufficient_data"


def _parse_date_flexible(date_str: str) -> datetime:
    """
    Parse date string with flexible format handling.

    Supports:
    - ISO format: 2015-07-01, 2015/07/01
    - US format: 07/01/2015, 7/1/2015
    - Text format: July 1, 2015, Jul 1 2015

    Args:
        date_str: Date string to parse

    Returns:
        datetime object

    Raises:
        ValueError: If date cannot be parsed
    """
    date_str = date_str.strip()

    # Try common formats explicitly first for better error messages
    formats = [
        "%Y-%m-%d",  # 2015-07-01
        "%Y/%m/%d",  # 2015/07/01
        "%m/%d/%Y",  # 07/01/2015
        "%m-%d-%Y",  # 07-01-2015
        "%d/%m/%Y",  # 01/07/2015 (UK format)
        "%d-%m-%Y",  # 01-07-2015
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Fall back to dateutil parser for text formats
    try:
        return parse_date(date_str)
    except Exception as e:
        raise ValueError(f"Could not parse date '{date_str}': {str(e)}")


def create_beta_index(prices: List[BetaPrice], frequency: str) -> BetaPriceIndex:
    """
    Create a BetaPriceIndex from parsed prices and user-confirmed frequency.

    Args:
        prices: List of BetaPrice objects (must be sorted by date)
        frequency: User-confirmed frequency

    Returns:
        BetaPriceIndex object with generated hash
    """
    index = BetaPriceIndex(
        prices=prices,
        frequency=frequency
    )

    # Generate hash
    index.generate_hash()

    return index


def validate_beta_coverage(
    investments: List,
    beta_index: BetaPriceIndex
) -> Tuple[bool, List[str]]:
    """
    Validate that beta data covers all investment periods.

    Args:
        investments: List of Investment objects
        beta_index: BetaPriceIndex to validate against

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if not beta_index.prices:
        errors.append("Beta index has no price data")
        return False, errors

    # Calculate beta midpoint range
    midpoints = [beta_index.calculate_midpoint(p.date) for p in beta_index.prices]
    beta_start = min(midpoints)
    beta_end = max(midpoints)

    # Track date range needed
    earliest_entry = None
    latest_exit = None

    # Check each investment
    for inv in investments:
        # Check entry date
        if inv.entry_date < beta_start:
            errors.append(
                f"Investment '{inv.investment_name}' entry date "
                f"({inv.entry_date.date()}) is before beta data start "
                f"({beta_start.date()})"
            )

        # Check latest date (exit/valuation)
        if inv.latest_date > beta_end:
            errors.append(
                f"Investment '{inv.investment_name}' latest date "
                f"({inv.latest_date.date()}) is after beta data end "
                f"({beta_end.date()})"
            )

        # Track overall range needed
        if earliest_entry is None or inv.entry_date < earliest_entry:
            earliest_entry = inv.entry_date
        if latest_exit is None or inv.latest_date > latest_exit:
            latest_exit = inv.latest_date

    # Add summary if there are errors
    if errors and earliest_entry and latest_exit:
        errors.append(
            f"\nBeta data needed: {earliest_entry.date()} to {latest_exit.date()}"
        )
        errors.append(
            f"Beta data available: {beta_start.date()} to {beta_end.date()}"
        )

    is_valid = len(errors) == 0
    return is_valid, errors
