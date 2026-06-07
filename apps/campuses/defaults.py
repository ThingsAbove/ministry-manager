from datetime import time

from apps.campuses.models import Weekday

# Seed data loaded by `manage.py setup_services` — edit here or via admin after setup.
DEFAULT_CAMPUS = {
    "address": "",
}

DEFAULT_SERVICE_TIMES = [
    {
        "name": "Sunday Service",
        "weekday": Weekday.SUNDAY,
        "start_time": time(22, 0),
        "duration_minutes": 90,
    },
]

DEFAULT_OCCURRENCE_WEEKS = 8
