import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def get_twilio_client():
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return None
    from twilio.rest import Client

    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_sms(to_number, body):
    client = get_twilio_client()
    if not client:
        logger.info("Twilio not configured; SMS skipped to %s: %s", to_number, body[:80])
        return None, "Twilio not configured"
    if not to_number:
        return None, "No phone number"
    try:
        kwargs = {"body": body, "to": to_number}
        if settings.TWILIO_MESSAGING_SERVICE_SID:
            kwargs["messaging_service_sid"] = settings.TWILIO_MESSAGING_SERVICE_SID
        elif settings.TWILIO_FROM_NUMBER:
            kwargs["from_"] = settings.TWILIO_FROM_NUMBER
        else:
            return None, "No Twilio sender configured"
        message = client.messages.create(**kwargs)
        return message.sid, None
    except Exception as exc:
        logger.exception("Twilio SMS failed")
        return None, str(exc)


def send_email(to_email, subject, body, html_body=None):
    if not to_email:
        return False, "No email address"
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_body or body,
            fail_silently=False,
        )
        return True, None
    except Exception as exc:
        logger.exception("Email send failed")
        return False, str(exc)


def dispatch_notification(notification):
    from .models import NotificationChannel, NotificationStatus

    notification.status = NotificationStatus.PENDING
    notification.save(update_fields=["status"])

    if notification.channel == NotificationChannel.SMS:
        phone = None
        if notification.recipient:
            if not notification.recipient.sms_opt_in:
                notification.status = NotificationStatus.SKIPPED
                notification.error_message = "SMS opt-out"
                notification.save()
                return notification
            phone = notification.recipient.contact_phone
        sid, error = send_sms(phone, notification.body)
        if sid:
            notification.status = NotificationStatus.SENT
            notification.external_id = sid
            notification.sent_at = timezone.now()
        else:
            notification.status = NotificationStatus.FAILED
            notification.error_message = error or "Unknown error"
    elif notification.channel == NotificationChannel.EMAIL:
        email = None
        if notification.recipient:
            if not notification.recipient.email_opt_in:
                notification.status = NotificationStatus.SKIPPED
                notification.error_message = "Email opt-out"
                notification.save()
                return notification
            email = notification.recipient.contact_email
        elif notification.recipient_user:
            email = notification.recipient_user.email
        ok, error = send_email(email, notification.subject, notification.body)
        if ok:
            notification.status = NotificationStatus.SENT
            notification.sent_at = timezone.now()
        else:
            notification.status = NotificationStatus.FAILED
            notification.error_message = error or "Unknown error"

    notification.save()
    return notification
