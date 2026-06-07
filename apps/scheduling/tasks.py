from datetime import date

from celery import shared_task

from .scheduler import run_auto_schedule_date_range, run_auto_schedule_for_occurrence


def _parse_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


@shared_task
def run_auto_schedule(occurrence_id=None, start_date=None, end_date=None):
    if occurrence_id:
        return run_auto_schedule_for_occurrence(occurrence_id)
    if start_date and end_date:
        return run_auto_schedule_date_range(_parse_date(start_date), _parse_date(end_date))
    raise ValueError("Provide occurrence_id or start_date and end_date")
