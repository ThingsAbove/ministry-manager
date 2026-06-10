# Ministry Manager

Web-based volunteer management system for church ministries. Built with Django, PostgreSQL, HTMX, Tailwind CSS, Celery, and Twilio.

## Features (Phase 1)

- Volunteer profiles with serving preferences and notification opt-ins
- Multi-campus service times and team/role management
- Block-out date calendar for availability
- Manual rota grid with conflict detection
- Greedy auto-scheduling (skills, certifications, block-outs, load balancing)
- SMS (Twilio) and email reminders with one-click RSVP links
- Mass messaging to teams
- Docker Compose for local development
- GitHub Actions CI/CD for Azure App Service deployment

## Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:8000 and create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

Generate service occurrences:

```bash
docker compose exec web python manage.py generate_occurrences --weeks=8
```

## Local Development (without Docker)

Requirements: Python 3.12–3.14, PostgreSQL 16, Redis, Node.js 22

Ensure PostgreSQL is running, then create the application database before migrating:

```bash
source .venv/bin/activate   # or use .venv/bin/python directly
pip install -r requirements.txt
cp .env.example .env
npm install && npm run build:css
python manage.py create_db    # creates ministry_manager in PostgreSQL
python manage.py migrate
python manage.py setup_groups   # auth groups, teams, campus, and Sunday service time
python manage.py createsuperuser
python manage.py runserver
```

`create_db` connects to PostgreSQL using `DATABASE_ADMIN_URL` (or `DATABASE_URL` if
unset) and creates the application role and database from `.env` when they do not
exist yet. Set `DATABASE_ADMIN_URL` to your local superuser, for example:

```
DATABASE_ADMIN_URL=postgres://postgres:yourpassword@localhost:5432/postgres
```

You can also create them manually:

```bash
psql -U postgres -c "CREATE USER ministry WITH PASSWORD 'ministry';"
psql -U postgres -c "CREATE DATABASE ministry_manager OWNER ministry;"
```

If the virtual environment does not exist yet:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run Celery worker and beat in separate terminals (uses PostgreSQL as the broker when
`CELERY_BROKER_URL` is not set; Docker Compose uses Redis instead):

```bash
celery -A ministry_manager worker -l info
celery -A ministry_manager beat -l info
```

To use Redis locally instead of PostgreSQL, set in `.env`:

```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection URL |
| `DATABASE_ADMIN_URL` | Superuser URL for `manage.py create_db` (local setup only) |
| `REDIS_URL` | Redis URL for Celery |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_MESSAGING_SERVICE_SID` | Twilio Messaging Service SID |
| `CHURCH_NAME` | Display name for the church |
| `CHURCH_TIMEZONE` | IANA timezone (e.g. `America/New_York`) |
| `REMINDER_DAYS_BEFORE` | Comma-separated days before shift to remind (default `7,1`) |

## Azure Deployment

1. Create Azure resources:
   - App Service (Linux, Docker)
   - Azure Database for PostgreSQL Flexible Server
   - Azure Cache for Redis
   - Azure Container Registry
   - Key Vault (optional, for secrets)

2. Configure App Service environment variables from `.env.example`.

3. Set GitHub secrets:
   - `AZURE_CREDENTIALS` — service principal JSON
   - `ACR_NAME` — container registry name
   - `AZURE_WEBAPP_NAME` — App Service name

4. Push to `main` to trigger CI/CD.

## Testing

```bash
source .venv/bin/activate
pytest
ruff check .
```

## Project Structure

```
apps/
  accounts/       User, VolunteerProfile
  campuses/       Campus, ServiceTime, ServiceOccurrence
  teams/          Team, TeamRole, Skills, Certifications
  scheduling/     Assignments, BlockOuts, Auto-scheduler
  communications/ Notifications, RSVP, Twilio/Email
  core/           Dashboard, ChurchSettings
```

## Documentation

- **[Operations Guide](docs/OPERATIONS_GUIDE.md)** — roles, admin setup, staffing workflow, volunteer onboarding, and day-to-day usage

## License

See [LICENSE](LICENSE).
