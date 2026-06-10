"""Demo volunteer definitions for seed_demo_volunteers management command."""

from apps.accounts.models import ServingFrequency

DEMO_EMAIL = "dev@hamradioqrp.com"
DEFAULT_DEMO_PASSWORD = "DemoVolunteer1!"

# (username, first_name, last_name, is_team_lead, serving_frequency)
_GREETERS = [
    ("demo-greeters-lead", "Alice", "Hartley", True, ServingFrequency.MONTHLY),
    ("demo-greeters-01", "Ben", "Collins", False, ServingFrequency.WEEKLY),
    ("demo-greeters-02", "Clara", "Nguyen", False, ServingFrequency.BIWEEKLY),
    ("demo-greeters-03", "Derek", "Walsh", False, ServingFrequency.MONTHLY),
]

_COFFEE = [
    ("demo-coffee-lead", "Elena", "Morales", True, ServingFrequency.MONTHLY),
    ("demo-coffee-01", "Frank", "Okafor", False, ServingFrequency.WEEKLY),
    ("demo-coffee-02", "Grace", "Patel", False, ServingFrequency.BIWEEKLY),
    ("demo-coffee-03", "Henry", "Sato", False, ServingFrequency.QUARTERLY),
]

_ROADIES = [
    ("demo-roadies-lead", "Iris", "Thompson", True, ServingFrequency.MONTHLY),
    ("demo-roadies-01", "Jack", "Rivera", False, ServingFrequency.WEEKLY),
    ("demo-roadies-02", "Kate", "Fischer", False, ServingFrequency.MONTHLY),
    ("demo-roadies-03", "Leo", "Chen", False, ServingFrequency.AS_NEEDED),
]

_SETUP = [
    ("demo-setup-lead", "Maya", "Brooks", True, ServingFrequency.MONTHLY),
    ("demo-setup-01", "Noah", "Kim", False, ServingFrequency.WEEKLY),
    ("demo-setup-02", "Olivia", "Grant", False, ServingFrequency.BIWEEKLY),
    ("demo-setup-03", "Paul", "Diaz", False, ServingFrequency.MONTHLY),
]

_TEARDOWN = [
    ("demo-teardown-lead", "Quinn", "Ashford", True, ServingFrequency.MONTHLY),
    ("demo-teardown-01", "Rachel", "Voss", False, ServingFrequency.WEEKLY),
    ("demo-teardown-02", "Sam", "Ellison", False, ServingFrequency.BIWEEKLY),
    ("demo-teardown-03", "Tara", "Mendez", False, ServingFrequency.MONTHLY),
]

_KID_CITY = [
    ("demo-kidcity-lead", "Uma", "Sinclair", True, ServingFrequency.MONTHLY),
    ("demo-kidcity-01", "Victor", "Lang", False, ServingFrequency.WEEKLY),
    ("demo-kidcity-02", "Wendy", "Cole", False, ServingFrequency.BIWEEKLY),
    ("demo-kidcity-03", "Xavier", "Reed", False, ServingFrequency.MONTHLY),
]

_TECH = [
    ("demo-tech-lead", "Yolanda", "Pierce", True, ServingFrequency.MONTHLY),
    ("demo-tech-01", "Zach", "Harmon", False, ServingFrequency.WEEKLY),
    ("demo-tech-02", "Abigail", "Frost", False, ServingFrequency.BIWEEKLY),
]

_WORSHIP = [
    ("demo-worship-lead", "Brian", "McAllister", True, ServingFrequency.MONTHLY),
    ("demo-worship-01", "Cynthia", "Hayes", False, ServingFrequency.WEEKLY),
    ("demo-worship-02", "Daniel", "Ruiz", False, ServingFrequency.MONTHLY),
]

TEAM_VOLUNTEER_SPECS = {
    "Greeters": _GREETERS,
    "Coffee": _COFFEE,
    "Roadies": _ROADIES,
    "Setup": _SETUP,
    "Teardown": _TEARDOWN,
    "Kid City": _KID_CITY,
    "Tech": _TECH,
    "Worship Team": _WORSHIP,
}


def all_demo_volunteers():
    volunteers = []
    for team_name, specs in TEAM_VOLUNTEER_SPECS.items():
        for username, first_name, last_name, is_team_lead, serving_frequency in specs:
            volunteers.append(
                {
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": DEMO_EMAIL,
                    "is_team_lead": is_team_lead,
                    "team_name": team_name,
                    "serving_frequency": serving_frequency,
                }
            )
    return volunteers
