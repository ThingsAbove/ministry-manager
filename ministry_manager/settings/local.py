from decouple import config as env_config

from .base import *  # noqa: F403

DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


def _postgresql_url_for_celery():
    db_url = env_config(
        "DATABASE_URL",
        default="postgres://ministry:ministry@localhost:5432/ministry_manager",
    )
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql+psycopg://", 1)
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return db_url


def _celery_database_urls():
    pg_url = _postgresql_url_for_celery()
    return f"sqla+{pg_url}", f"db+{pg_url}"


# Local dev without Docker/Redis: use PostgreSQL as the Celery broker and result
# backend. Docker Compose sets CELERY_BROKER_URL to Redis explicitly.
_broker = env_config("CELERY_BROKER_URL", default="")
_backend = env_config("CELERY_RESULT_BACKEND", default="")

if not _broker:
    CELERY_BROKER_URL, CELERY_RESULT_BACKEND = _celery_database_urls()
else:
    CELERY_BROKER_URL = _broker
    CELERY_RESULT_BACKEND = _backend or _broker
