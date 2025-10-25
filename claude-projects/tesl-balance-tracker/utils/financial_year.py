"""
Financial year utilities

Handles Australian financial year calculations and date operations.
"""

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import Tuple

from ..config.settings import get_config


def get_financial_year(ref_date: date = None) -> int:
    """
    Get financial year for a given date

    Australian financial year runs from July 1 to June 30.
    FY 2024 = July 1, 2023 to June 30, 2024

    Args:
        ref_date: Reference date (defaults to today)

    Returns:
        int: Financial year (e.g., 2024)
    """
    config = get_config()
    if ref_date is None:
        ref_date = date.today()

    fy_start_month = config.entitlements.financial_year_start_month
    fy_start_day = config.entitlements.financial_year_start_day

    # If before July 1, FY is current year, otherwise next year
    if ref_date.month < fy_start_month or \
       (ref_date.month == fy_start_month and ref_date.day < fy_start_day):
        return ref_date.year
    else:
        return ref_date.year + 1


def get_current_financial_year() -> int:
    """Get current financial year"""
    return get_financial_year()


def get_financial_year_dates(financial_year: int) -> Tuple[date, date]:
    """
    Get start and end dates for a financial year

    Args:
        financial_year: Financial year (e.g., 2024)

    Returns:
        Tuple of (start_date, end_date)
    """
    config = get_config()
    fy_start_month = config.entitlements.financial_year_start_month
    fy_start_day = config.entitlements.financial_year_start_day

    # FY 2024 = July 1, 2023 to June 30, 2024
    start_date = date(financial_year - 1, fy_start_month, fy_start_day)
    end_date = date(financial_year, fy_start_month, fy_start_day) - relativedelta(days=1)

    return start_date, end_date


def calculate_days_in_financial_year(financial_year: int) -> int:
    """
    Calculate number of days in a financial year

    Args:
        financial_year: Financial year

    Returns:
        int: Number of days in the financial year
    """
    start_date, end_date = get_financial_year_dates(financial_year)
    return (end_date - start_date).days + 1


def calculate_days_employed(start_date: date, end_date: date, financial_year: int) -> int:
    """
    Calculate number of days employed within a financial year

    Args:
        start_date: Employment start date
        end_date: Employment end date (or None if still employed)
        financial_year: Financial year to calculate for

    Returns:
        int: Number of days employed in the financial year
    """
    fy_start, fy_end = get_financial_year_dates(financial_year)

    # Determine effective start and end within FY
    effective_start = max(start_date, fy_start)
    effective_end = min(end_date if end_date else fy_end, fy_end)

    # If no overlap, return 0
    if effective_start > effective_end:
        return 0

    return (effective_end - effective_start).days + 1


def calculate_prorata_factor(
    start_date: date,
    end_date: date,
    financial_year: int,
    fte: float = 1.0
) -> float:
    """
    Calculate pro-rata factor for entitlement calculation

    Considers both partial year employment and FTE.

    Args:
        start_date: Employment start date
        end_date: Employment end date (or None if still employed)
        financial_year: Financial year
        fte: Full-time equivalent (0.0 to 1.0)

    Returns:
        float: Pro-rata factor (0.0 to 1.0)
    """
    config = get_config()

    factor = 1.0

    # Apply FTE factor if enabled
    if config.entitlements.enable_fte_prorata:
        factor *= fte

    # Apply partial year factor if enabled
    if config.entitlements.enable_partial_year_prorata:
        days_employed = calculate_days_employed(start_date, end_date, financial_year)
        days_in_fy = calculate_days_in_financial_year(financial_year)
        if days_in_fy > 0:
            factor *= (days_employed / days_in_fy)

    return min(factor, 1.0)  # Cap at 1.0


def months_until_year_end(ref_date: date = None) -> int:
    """
    Calculate months until end of current financial year

    Args:
        ref_date: Reference date (defaults to today)

    Returns:
        int: Number of full months until year end
    """
    if ref_date is None:
        ref_date = date.today()

    fy = get_financial_year(ref_date)
    _, fy_end = get_financial_year_dates(fy)

    # Calculate months difference
    months = (fy_end.year - ref_date.year) * 12 + (fy_end.month - ref_date.month)

    return max(0, months)


def format_financial_year(financial_year: int) -> str:
    """
    Format financial year for display

    Args:
        financial_year: Financial year (e.g., 2024)

    Returns:
        str: Formatted string (e.g., "FY 2023/24")
    """
    prev_year = financial_year - 1
    return f"FY {prev_year}/{str(financial_year)[-2:]}"


def parse_financial_year(fy_string: str) -> int:
    """
    Parse financial year from string

    Args:
        fy_string: String like "FY 2023/24" or "2024"

    Returns:
        int: Financial year
    """
    # Remove "FY" prefix if present
    fy_string = fy_string.replace("FY", "").strip()

    # Handle "2023/24" format
    if "/" in fy_string:
        return int(fy_string.split("/")[0]) + 1

    # Handle "2024" format
    return int(fy_string)
