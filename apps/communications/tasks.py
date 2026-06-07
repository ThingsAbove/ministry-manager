from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.scheduling.models import Assignment, AssignmentStatus

from .models import (
    RSVP,
    Notification,
    NotificationChannel,
    NotificationType,
)
from .services import dispatch_notification
from .tokens import generate_rsvp_token


def _assignment_message(assignment, include_rsvp=False):
    occ = assignment.service_occurrence
    role = assignment.team_role
    lines = [
        f"You are scheduled for {role.team.name} — {role.name}",
        f"Service: {occ.service_time.name}",
        f"Date: {occ.date.strftime('%A, %B %d, %Y')} at {occ.start_time.strftime('%I:%M %p')}",
        f"Campus: {occ.service_time.campus.name}",
    ]
    if include_rsvp:
        token = generate_rsvp_token(assignment.pk)
        base = settings.CSRF_TRUSTED_ORIGINS[0] if settings.CSRF_TRUSTED_ORIGINS else "http://localhost:8000"
        lines.append(f"Accept: {base}/communications/rsvp/{token}/accept/")
        lines.append(f"Decline: {base}/communications/rsvp/{token}/decline/")
    return "\n".join(lines)


def notify_assignment(assignment):
    if not assignment.volunteer_id:
        return []
    RSVP.objects.get_or_create(assignment=assignment)
    body = _assignment_message(assignment, include_rsvp=True)
    role_name = assignment.team_role.name
    occ_date = assignment.service_occurrence.date
    subject = f"Volunteer shift: {role_name} on {occ_date}"
    notifications = []

    if assignment.volunteer.sms_opt_in and assignment.volunteer.contact_phone:
        n = Notification.objects.create(
            recipient=assignment.volunteer,
            assignment=assignment,
            notification_type=NotificationType.ASSIGNMENT,
            channel=NotificationChannel.SMS,
            body=body,
        )
        dispatch_notification(n)
        notifications.append(n)

    if assignment.volunteer.email_opt_in and assignment.volunteer.contact_email:
        n = Notification.objects.create(
            recipient=assignment.volunteer,
            assignment=assignment,
            notification_type=NotificationType.ASSIGNMENT,
            channel=NotificationChannel.EMAIL,
            subject=subject,
            body=body,
        )
        dispatch_notification(n)
        notifications.append(n)

    return notifications


@shared_task
def send_shift_reminders():
    today = timezone.localdate()
    sent = 0
    for days_before in settings.REMINDER_DAYS_BEFORE:
        target_date = today + timedelta(days=days_before)
        assignments = Assignment.objects.filter(
            service_occurrence__date=target_date,
            volunteer__isnull=False,
            status=AssignmentStatus.SCHEDULED,
        ).select_related("volunteer", "service_occurrence__service_time__campus", "team_role__team")

        for assignment in assignments:
            already = Notification.objects.filter(
                assignment=assignment,
                notification_type=NotificationType.REMINDER,
                created_at__date=today,
            ).exists()
            if already:
                continue

            day_label = "day" if days_before == 1 else "days"
            prefix = f"Reminder ({days_before} {day_label}): "
            body = prefix + _assignment_message(assignment, include_rsvp=True)
            subject = f"Shift reminder: {assignment.service_occurrence.date}"

            volunteer = assignment.volunteer
            for channel, opt_in, contact in [
                (NotificationChannel.SMS, volunteer.sms_opt_in, volunteer.contact_phone),
                (NotificationChannel.EMAIL, volunteer.email_opt_in, volunteer.contact_email),
            ]:
                if not opt_in or not contact:
                    continue
                n = Notification.objects.create(
                    recipient=assignment.volunteer,
                    assignment=assignment,
                    notification_type=NotificationType.REMINDER,
                    channel=channel,
                    subject=subject,
                    body=body,
                )
                dispatch_notification(n)
                sent += 1
    return {"sent": sent}


@shared_task
def send_unfilled_slot_alerts():
    today = timezone.localdate()
    end = today + timedelta(days=7)
    unfilled = Assignment.objects.filter(
        volunteer__isnull=True,
        service_occurrence__date__gte=today,
        service_occurrence__date__lte=end,
    ).select_related("team_role__team", "service_occurrence")

    sent = 0
    notified_teams = set()
    for assignment in unfilled:
        team = assignment.team_role.team
        if team.pk in notified_teams:
            continue
        for leader in team.leaders.all():
            occ = assignment.service_occurrence
            body = (
                f"Unfilled slot: {assignment.team_role.name} on "
                f"{occ.date} ({occ.service_time.name})"
            )
            n = Notification.objects.create(
                recipient_user=leader,
                assignment=assignment,
                notification_type=NotificationType.UNFILLED,
                channel=NotificationChannel.EMAIL,
                subject="Unfilled volunteer slot",
                body=body,
            )
            dispatch_notification(n)
            sent += 1
        notified_teams.add(team.pk)
    return {"sent": sent}


@shared_task
def send_mass_message(team_id, message, channels, sender_user_id):
    from apps.teams.models import Team

    team = Team.objects.get(pk=team_id)
    memberships = team.memberships.filter(is_active=True).select_related("volunteer")
    sent = 0
    for membership in memberships:
        volunteer = membership.volunteer
        subject = f"Message from {team.name}"
        if "sms" in channels and volunteer.sms_opt_in and volunteer.contact_phone:
            n = Notification.objects.create(
                recipient=volunteer,
                notification_type=NotificationType.MASS,
                channel=NotificationChannel.SMS,
                body=message,
            )
            dispatch_notification(n)
            sent += 1
        if "email" in channels and volunteer.email_opt_in and volunteer.contact_email:
            n = Notification.objects.create(
                recipient=volunteer,
                notification_type=NotificationType.MASS,
                channel=NotificationChannel.EMAIL,
                subject=subject,
                body=message,
            )
            dispatch_notification(n)
            sent += 1
    return {"sent": sent}
