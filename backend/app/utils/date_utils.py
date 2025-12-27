from datetime import date


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
