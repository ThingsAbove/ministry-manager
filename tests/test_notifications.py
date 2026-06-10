from datetime import timedelta

import pytest
from django.conf import settings
from django.core import mail
from django.utils import timezone

from apps.accounts.models import User
from apps.communications.models import Notification, NotificationType
from apps.communications.services import dispatch_notification, resolve_email_delivery
from apps.communications.tasks import (
    notify_assignment,
    send_shift_reminders,
    send_unfilled_slot_alerts,
)
from apps.communications.tokens import generate_rsvp_token
from apps.scheduling.models import Assignment
from apps.scheduling.scheduler import ensure_assignment_slots
from apps.scheduling.signals import suppress_assignment_notifications
from apps.teams.models import TeamMembership


@pytest.mark.django_db
class TestEmailRouting:
    def test_resolve_email_delivery_for_test_user(self, make_volunteer):
        user = make_volunteer(
            username="test-routing",
            is_test_user=True,
            first_name="Test",
            last_name="User",
        )
        email, subject = resolve_email_delivery(user, "Shift reminder")
        assert email == settings.TEST_EMAIL_ADDRESS
        assert "[Test:test-routing]" in subject
        assert "Test User" in subject

    def test_resolve_email_delivery_for_real_user(self, make_volunteer):
        user = make_volunteer(username="real-user", email="real@example.com")
        email, subject = resolve_email_delivery(user, "Shift reminder")
        assert email == "real@example.com"
        assert subject == "Shift reminder"

    def test_dispatch_notification_routes_test_user_email(self, make_volunteer):
        user = make_volunteer(
            username="test-notify",
            is_test_user=True,
            first_name="Demo",
            last_name="Volunteer",
        )
        profile = user.volunteer_profile
        profile.email_opt_in = True
        profile.save()

        notification = Notification.objects.create(
            recipient=profile,
            notification_type=NotificationType.REMINDER,
            channel="email",
            subject="Test subject",
            body="Test body",
        )
        dispatch_notification(notification)

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [settings.TEST_EMAIL_ADDRESS]
        assert "[Test:test-notify]" in mail.outbox[0].subject


@pytest.mark.django_db
class TestShiftReminders:
    def test_send_shift_reminders(self, volunteer, team, role, occurrence):
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        volunteer.email_opt_in = True
        volunteer.save()
        with suppress_assignment_notifications():
            Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=volunteer,
                slot_index=0,
            )
        occurrence.date = timezone.localdate() + timedelta(days=7)
        occurrence.save()

        result = send_shift_reminders()
        assert result["sent"] >= 1
        assert Notification.objects.filter(recipient=volunteer).exists()


@pytest.mark.django_db
class TestUnfilledSlotAlerts:
    def test_send_unfilled_slot_alerts(self, make_team_leader, team, role, occurrence):
        leader = make_team_leader(team, username="unfilled-lead", is_test_user=True)
        leader.email = settings.TEST_EMAIL_ADDRESS
        leader.save()
        ensure_assignment_slots(occurrence)
        occurrence.date = timezone.localdate() + timedelta(days=3)
        occurrence.save()

        result = send_unfilled_slot_alerts()
        assert result["sent"] >= 1
        assert Notification.objects.filter(
            recipient_user=leader,
            notification_type=NotificationType.UNFILLED,
        ).exists()


@pytest.mark.django_db
class TestDeclineNotifications:
    def test_decline_notifies_leader(
        self, make_team_leader, volunteer, team, role, occurrence, client
    ):
        leader = make_team_leader(team, username="decline-lead", is_test_user=True)
        leader.email = settings.TEST_EMAIL_ADDRESS
        leader.save()
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        with suppress_assignment_notifications():
            assignment = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=volunteer,
                slot_index=0,
            )

        mail.outbox.clear()
        token = generate_rsvp_token(assignment.pk)
        response = client.get(
            f"/communications/rsvp/{token}/decline/",
            HTTP_HOST="localhost",
        )
        assert response.status_code == 200
        assert Notification.objects.filter(
            recipient_user=leader,
            notification_type=NotificationType.RSVP,
        ).exists()
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [settings.TEST_EMAIL_ADDRESS]


@pytest.mark.django_db
class TestAssignmentNotifications:
    def test_notify_assignment_sends_email_with_rsvp_links(
        self, volunteer, team, role, occurrence
    ):
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        volunteer.email_opt_in = True
        volunteer.save()
        with suppress_assignment_notifications():
            assignment = Assignment.objects.create(
                service_occurrence=occurrence,
                team_role=role,
                volunteer=volunteer,
                slot_index=0,
            )

        mail.outbox.clear()
        notify_assignment(assignment)
        assert Notification.objects.filter(
            recipient=volunteer,
            notification_type=NotificationType.ASSIGNMENT,
        ).exists()
        assert len(mail.outbox) == 1
        assert b"/communications/rsvp/" in mail.outbox[0].body.encode()

    def test_assignment_save_triggers_notification(self, volunteer, team, role, occurrence):
        TeamMembership.objects.create(team=team, volunteer=volunteer)
        volunteer.email_opt_in = True
        volunteer.save()
        mail.outbox.clear()
        Assignment.objects.create(
            service_occurrence=occurrence,
            team_role=role,
            volunteer=volunteer,
            slot_index=0,
        )
        assert Notification.objects.filter(
            recipient=volunteer,
            notification_type=NotificationType.ASSIGNMENT,
        ).exists()
        assert len(mail.outbox) == 1

    def test_admin_not_notified_as_volunteer(self, team, role, occurrence, make_volunteer):
        admin = User.objects.create_user(
            username="admin-only",
            password="pass",
            email="admin@example.com",
            is_staff=True,
        )
        volunteer = make_volunteer(username="assigned-vol")
        TeamMembership.objects.create(team=team, volunteer=volunteer.volunteer_profile)
        volunteer.volunteer_profile.email_opt_in = True
        volunteer.volunteer_profile.save()

        mail.outbox.clear()
        Assignment.objects.create(
            service_occurrence=occurrence,
            team_role=role,
            volunteer=volunteer.volunteer_profile,
            slot_index=0,
        )

        assert not Notification.objects.filter(recipient_user=admin).exists()
        assert all(admin.email not in message.to for message in mail.outbox)
