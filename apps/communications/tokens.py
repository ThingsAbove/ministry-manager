from django.conf import settings
from django.core import signing
from django.urls import reverse


def generate_rsvp_token(assignment_id):
    return signing.dumps({"assignment_id": assignment_id}, salt="rsvp")


def verify_rsvp_token(token, max_age=None):
    max_age = max_age or settings.RSVP_TOKEN_MAX_AGE
    return signing.loads(token, salt="rsvp", max_age=max_age)


def build_rsvp_urls(request, assignment_id):
    token = generate_rsvp_token(assignment_id)
    accept = request.build_absolute_uri(
        reverse("communications:rsvp_accept", kwargs={"token": token})
    )
    decline = request.build_absolute_uri(
        reverse("communications:rsvp_decline", kwargs={"token": token})
    )
    return accept, decline
