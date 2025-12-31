from datetime import date, timedelta
from dateutil.parser import parse


def is_working_day(d: date) -> bool:
    """
    Checks if a given date is a working day (Monday to Friday).

    Args:
        d: The date to check.

    Returns:
        True if the date is a weekday, False otherwise.
    """
    # weekday() returns 0 for Monday and 6 for Sunday.
    return d.weekday() < 5


def count_working_days(start_date_str: str, end_date_str: str) -> int:
    """
    Calculates the number of working days between a start and end date, inclusive.
    """
    try:
        start_date = parse(start_date_str).date()
        end_date = parse(end_date_str).date()
    except (ValueError, TypeError):
        return 0

    if start_date > end_date:
        return 0

    working_days = 0
    current_date = start_date
    while current_date <= end_date:
        if is_working_day(current_date):
            working_days += 1
        current_date += timedelta(days=1)
    return working_days
