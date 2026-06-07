from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Max, Min

from apps.campuses.models import ServiceOccurrence, ServiceTime


class Command(BaseCommand):
    help = "Generate service occurrences from recurring service times"

    def add_arguments(self, parser):
        parser.add_argument(
            "--weeks",
            type=int,
            default=8,
            help="Number of weeks ahead to generate (default: 8)",
        )
        parser.add_argument(
            "--start",
            type=str,
            default=None,
            help=(
                "Start date YYYY-MM-DD (default: today, or day after last "
                "occurrence with --extend)"
            ),
        )
        parser.add_argument(
            "--extend",
            action="store_true",
            help="Generate from the day after the latest existing occurrence",
        )

    def handle(self, *args, **options):
        weeks = options["weeks"]
        today = date.today()

        if options["start"]:
            start = date.fromisoformat(options["start"])
        elif options["extend"]:
            last = ServiceOccurrence.objects.aggregate(last=Max("date"))["last"]
            start = (last + timedelta(days=1)) if last else today
        else:
            start = today

        end = start + timedelta(weeks=weeks)
        created = 0
        active_times = ServiceTime.objects.filter(is_active=True).select_related("campus")

        if not active_times.exists():
            self.stdout.write(self.style.WARNING("No active service times configured."))
            return

        for service_time in active_times:
            current = start
            while current <= end:
                if current.weekday() == service_time.weekday:
                    _, was_created = ServiceOccurrence.objects.get_or_create(
                        service_time=service_time,
                        date=current,
                        defaults={"start_time": service_time.start_time},
                    )
                    if was_created:
                        created += 1
                current += timedelta(days=1)

        stats = ServiceOccurrence.objects.aggregate(
            earliest=Min("date"),
            latest=Max("date"),
            total=Max("id"),
        )
        total = ServiceOccurrence.objects.count()

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {created} new service occurrence(s) "
                    f"({start.isoformat()} through {end.isoformat()})."
                )
            )
        else:
            self.stdout.write(
                f"No new occurrences needed for {start.isoformat()} through {end.isoformat()} "
                f"(all dates already exist)."
            )

        if total:
            self.stdout.write(
                f"Schedule coverage: {total} occurrence(s), "
                f"{stats['earliest']} through {stats['latest']}."
            )
            if stats["latest"] and stats["latest"] < today + timedelta(weeks=2):
                self.stdout.write(
                    self.style.WARNING(
                        "Less than 2 weeks of future occurrences remain. "
                        "Run with --extend to add more."
                    )
                )
        else:
            self.stdout.write(self.style.WARNING("No service occurrences in the database yet."))
