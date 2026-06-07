from django.core.management.base import BaseCommand

from apps.teams.defaults import DEFAULT_TEAMS
from apps.teams.models import Team, TeamRole


class Command(BaseCommand):
    help = "Create default volunteer teams and roles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Deactivate existing default teams before re-creating missing roles",
        )

    def handle(self, *args, **options):
        teams_created = 0
        roles_created = 0

        default_names = {t["name"] for t in DEFAULT_TEAMS}

        if options["reset"]:
            deactivated = Team.objects.filter(name__in=default_names, is_active=True).update(
                is_active=False
            )
            if deactivated:
                self.stdout.write(f"Deactivated {deactivated} existing default team(s).")

        for team_data in DEFAULT_TEAMS:
            team, team_was_created = Team.objects.get_or_create(
                name=team_data["name"],
                defaults={
                    "description": team_data["description"],
                    "is_active": True,
                },
            )

            if team_was_created:
                teams_created += 1
                self.stdout.write(self.style.SUCCESS(f"Created team: {team.name}"))
            else:
                updated = False
                if team.description != team_data["description"]:
                    team.description = team_data["description"]
                    updated = True
                if not team.is_active:
                    team.is_active = True
                    updated = True
                if updated:
                    team.save()
                self.stdout.write(f"Team already exists: {team.name}")

            for role_data in team_data["roles"]:
                role, role_was_created = TeamRole.objects.get_or_create(
                    team=team,
                    name=role_data["name"],
                    defaults={
                        "description": role_data.get("description", ""),
                        "slots_per_service": role_data.get("slots_per_service", 1),
                    },
                )
                if role_was_created:
                    roles_created += 1
                    self.stdout.write(f"  + role: {role.name} ({role.slots_per_service} slots)")
                else:
                    changed = False
                    if role.description != role_data.get("description", ""):
                        role.description = role_data.get("description", "")
                        changed = True
                    slots = role_data.get("slots_per_service", 1)
                    if role.slots_per_service != slots:
                        role.slots_per_service = slots
                        changed = True
                    if changed:
                        role.save()
                        self.stdout.write(f"  ~ updated role: {role.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {teams_created} team(s) and {roles_created} role(s) created."
            )
        )
