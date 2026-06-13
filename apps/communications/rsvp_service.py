from django.utils import timezone

from .models import RSVP, Notification, NotificationChannel, NotificationType, RSVPStatus
from .services import dispatch_notification


def notify_leaders_of_decline(assignment):
    team = assignment.team_role.team
    occ_date = assignment.service_occurrence.date
    decline_body = f"{assignment.volunteer} declined {assignment.team_role.name} on {occ_date}"
    for leader in team.leaders.all():
        notification = Notification.objects.create(
            recipient_user=leader,
            assignment=assignment,
            notification_type=NotificationType.RSVP,
            channel=NotificationChannel.EMAIL,
            subject="Volunteer declined shift",
            body=decline_body,
        )
        dispatch_notification(notification)


def record_rsvp(assignment, accept):
    rsvp, _ = RSVP.objects.get_or_create(assignment=assignment)
    previous_status = rsvp.status
    rsvp.status = RSVPStatus.ACCEPTED if accept else RSVPStatus.DECLINED
    rsvp.responded_at = timezone.now()
    rsvp.save()

    if not accept and previous_status != RSVPStatus.DECLINED:
        notify_leaders_of_decline(assignment)

    return rsvp
