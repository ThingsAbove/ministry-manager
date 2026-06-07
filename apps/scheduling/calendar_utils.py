from datetime import timedelta


def month_calendar_weeks(first_of_month, last_of_month):
    """Return weeks as lists of date objects (None for padding cells)."""
    start = first_of_month - timedelta(days=first_of_month.weekday())
    end = last_of_month + timedelta(days=(6 - last_of_month.weekday()))
    weeks = []
    current = start
    while current <= end:
        week = []
        for _ in range(7):
            if first_of_month <= current <= last_of_month:
                week.append(current)
            else:
                week.append(None)
            current += timedelta(days=1)
        weeks.append(week)
    return weeks


def shift_month(year, month, delta):
    month += delta
    while month < 1:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    return year, month
