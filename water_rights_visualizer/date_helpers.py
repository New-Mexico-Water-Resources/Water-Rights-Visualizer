import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


def get_one_month_slice(year: int, month: int) -> slice:
    """
    Get the start (inclusive) and end (not inclusive) indices for a given month.

    Args:
        year (int): The year for which the slice is generated.
        month (int): The month for which the slice is generated (1-12).

    Returns:
        (start_index, end): The slice for the given month (start <= x < end).
    """
    start = datetime(year, month, 1).date()
    start_index = start.timetuple().tm_yday - 1

    end = start + relativedelta(months=1) - relativedelta(days=1)
    end_index = end.timetuple().tm_yday

    return start_index, end_index


def get_days_in_month(year: int, month: int) -> int:
    """
    Get the number of days in a month.
    """
    start, end = get_one_month_slice(year, month)

    return end - start


def get_days_in_year(year: int) -> int:
    """
    Get the number of days in a year.
    """
    start = datetime(year, 1, 1).date()
    end = datetime(year, 12, 31).date()

    return (end - start).days + 1


def get_day_of_year(year: int, month: int, day: int) -> int:
    """
    Get the day of the year for a given date.
    """
    day_of_year = (datetime(year, month, day) - datetime(year, 1, 1)).days

    return day_of_year
