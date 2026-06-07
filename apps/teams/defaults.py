"""Default volunteer teams and roles for Ministry Manager."""

DEFAULT_TEAMS = [
    {
        "name": "Greeters",
        "description": "Welcome guests, answer questions, and assist with seating.",
        "roles": [
            {
                "name": "Door Greeter",
                "slots_per_service": 2,
                "description": "Welcome people at entrances.",
            },
            {
                "name": "Usher",
                "slots_per_service": 2,
                "description": "Help guests find seats and manage flow.",
            },
        ],
    },
    {
        "name": "Coffee",
        "description": "Prepare and serve coffee and refreshments.",
        "roles": [
            {
                "name": "Barista",
                "slots_per_service": 2,
                "description": "Brew and serve coffee.",
            },
            {
                "name": "Counter Help",
                "slots_per_service": 1,
                "description": "Assist at the counter and restock.",
            },
        ],
    },
    {
        "name": "Roadies",
        "description": "Load-in, stage support, and production assistance.",
        "roles": [
            {
                "name": "Stage Hand",
                "slots_per_service": 2,
                "description": "Stage setup and instrument changes.",
            },
            {
                "name": "Runner",
                "slots_per_service": 1,
                "description": "General production support.",
            },
        ],
    },
    {
        "name": "Setup",
        "description": "Prepare the building and rooms before services.",
        "roles": [
            {
                "name": "Setup Crew",
                "slots_per_service": 4,
                "description": "Chairs, signage, and room preparation.",
            },
        ],
    },
    {
        "name": "Teardown",
        "description": "Reset and clean up after services.",
        "roles": [
            {
                "name": "Teardown Crew",
                "slots_per_service": 4,
                "description": "Break down and store equipment and furniture.",
            },
        ],
    },
    {
        "name": "Kid City",
        "description": "Children's ministry classrooms and check-in.",
        "roles": [
            {
                "name": "Small Group Leader",
                "slots_per_service": 3,
                "description": "Lead a children's small group.",
            },
            {
                "name": "Check-In",
                "slots_per_service": 2,
                "description": "Register and check in children.",
            },
            {
                "name": "Floater",
                "slots_per_service": 1,
                "description": "Support across classrooms as needed.",
            },
        ],
    },
    {
        "name": "Tech",
        "description": "Audio, video, lighting, and presentation.",
        "roles": [
            {
                "name": "Sound Engineer",
                "slots_per_service": 1,
                "description": "Mix front-of-house audio.",
            },
            {
                "name": "Presentation",
                "slots_per_service": 1,
                "description": "Slides and lyric presentation.",
            },
            {
                "name": "Lighting",
                "slots_per_service": 1,
                "description": "Stage lighting operation.",
            },
        ],
    },
    {
        "name": "Worship Team",
        "description": "Lead the congregation in worship through music.",
        "roles": [
            {
                "name": "Vocals",
                "slots_per_service": 3,
                "description": "Worship vocalist.",
            },
            {
                "name": "Band",
                "slots_per_service": 4,
                "description": "Instrumentalist on worship team.",
            },
            {
                "name": "Worship Leader",
                "slots_per_service": 1,
                "description": "Lead the worship set.",
            },
        ],
    },
]
