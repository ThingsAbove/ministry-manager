import dj_database_url
import psycopg
from decouple import config
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from psycopg import sql


def _conn_params(parsed, dbname="postgres"):
    params = {
        "dbname": dbname,
        "user": parsed.get("USER"),
        "password": parsed.get("PASSWORD"),
        "host": parsed.get("HOST"),
        "port": parsed.get("PORT") or 5432,
    }
    options = parsed.get("OPTIONS") or {}
    if options.get("sslmode"):
        params["sslmode"] = options["sslmode"]
    return {k: v for k, v in params.items() if v is not None}


def _role_exists(cur, role):
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,))
    return cur.fetchone() is not None


def _database_exists(cur, db_name):
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    return cur.fetchone() is not None


class Command(BaseCommand):
    help = "Create the PostgreSQL role and database if they do not exist"

    def handle(self, *args, **options):
        db = settings.DATABASES["default"]
        engine = db.get("ENGINE", "")

        if "postgresql" not in engine and "postgis" not in engine:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipping database creation — engine is {engine!r}, not PostgreSQL."
                )
            )
            return

        db_name = db["NAME"]
        db_user = db.get("USER")
        db_password = db.get("PASSWORD")

        if not db_name or not db_user:
            raise CommandError("DATABASE_URL must include a database name and user.")

        admin_url = config("DATABASE_ADMIN_URL", default="")
        if admin_url:
            admin_parsed = dj_database_url.parse(admin_url)
        else:
            admin_parsed = db

        self.stdout.write(f"Ensuring PostgreSQL role {db_user!r} and database {db_name!r}...")

        try:
            with psycopg.connect(
                **_conn_params(admin_parsed),
                autocommit=True,
            ) as conn:
                with conn.cursor() as cur:
                    if not _role_exists(cur, db_user):
                        cur.execute(
                            sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
                                sql.Identifier(db_user),
                                sql.Literal(db_password or ""),
                            )
                        )
                        self.stdout.write(self.style.SUCCESS(f"Created role {db_user!r}."))
                    else:
                        self.stdout.write(f"Role {db_user!r} already exists.")

                    if _database_exists(cur, db_name):
                        self.stdout.write(
                            self.style.SUCCESS(f"Database {db_name!r} already exists.")
                        )
                        return

                    cur.execute(
                        sql.SQL("CREATE DATABASE {} OWNER {}").format(
                            sql.Identifier(db_name),
                            sql.Identifier(db_user),
                        )
                    )
        except psycopg.OperationalError as exc:
            raise CommandError(
                "Could not connect to PostgreSQL. Ensure the server is running and "
                "set DATABASE_ADMIN_URL in .env to a superuser connection, e.g.\n"
                "  DATABASE_ADMIN_URL=postgres://postgres:yourpassword@localhost:5432/postgres\n"
                f"Original error: {exc}"
            ) from exc

        self.stdout.write(self.style.SUCCESS(f"Created database {db_name!r}."))
