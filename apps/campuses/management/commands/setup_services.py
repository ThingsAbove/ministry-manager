from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.campuses.defaults import DEFAULT_CAMPUS, DEFAULT_OCCURRENCE_WEEKS, DEFAULT_SERVICE_TIMES
from apps.campuses.models import Campus, ServiceTime


class Command(BaseCommand):
    help = "Create default campus and service times from seed configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--weeks",
            type=int,
            default=DEFAULT_OCCURRENCE_WEEKS,
            help="Weeks of service occurrences to generate (default: 8)",
        )
        parser.add_argument(
            "--extend",
            action="store_true",
            help="Generate occurrences starting after the latest existing date",
        )
        parser.add_argument(
            "--no-occurrences",
            action="store_true",
            help="Skip generating ServiceOccurrence rows",
        )

    def handle(self, *args, **options):
        campus_name = settings.CHURCH_NAME
        campus, campus_created = Campus.objects.get_or_create(
            name=campus_name,
            defaults={
                "address": DEFAULT_CAMPUS.get("address", ""),
                "is_active": True,
            },
        )
        if campus_created:
            self.stdout.write(self.style.SUCCESS(f"Created campus: {campus.name}"))
        else:
            if not campus.is_active:
                campus.is_active = True
                campus.save(update_fields=["is_active"])
            self.stdout.write(f"Campus already exists: {campus.name}")

        times_created = 0
        for entry in DEFAULT_SERVICE_TIMES:
            service_time, created = ServiceTime.objects.get_or_create(
                campus=campus,
                name=entry["name"],
                weekday=entry["weekday"],
                start_time=entry["start_time"],
                defaults={
                    "duration_minutes": entry.get("duration_minutes", 90),
                    "is_active": True,
                },
            )
            if created:
                times_created += 1
                weekday = service_time.get_weekday_display()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  + {service_time.name}: {weekday} "
                        f"{service_time.start_time.strftime('%I:%M %p').lstrip('0')}"
                    )
                )
            else:
                changed = False
                duration = entry.get("duration_minutes", 90)
                if service_time.duration_minutes != duration:
                    service_time.duration_minutes = duration
                    changed = True
                if not service_time.is_active:
                    service_time.is_active = True
                    changed = True
                if changed:
                    service_time.save()
                weekday = service_time.get_weekday_display()
                start_label = service_time.start_time.strftime("%I:%M %p").lstrip("0")
                self.stdout.write(
                    f"  Service time already exists: {service_time.name} "
                    f"({weekday} {start_label})"
                )

        if not options["no_occurrences"]:
            self.stdout.write(f"Generating occurrences for {options['weeks']} weeks...")
            gen_kwargs = {"weeks": options["weeks"]}
            if options["extend"]:
                gen_kwargs["extend"] = True
            call_command("generate_occurrences", **gen_kwargs)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Campus ready with {times_created} new service time(s)."
            )
        )
