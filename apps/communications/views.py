from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.scheduling.models import Assignment
from apps.teams.models import Team

from .rsvp_service import record_rsvp
from .tasks import send_mass_message
from .tokens import verify_rsvp_token


def is_leader_or_staff(user):
    return user.is_staff or user.is_team_leader()


class MassMessageForm(forms.Form):
    team = forms.ModelChoiceField(queryset=Team.objects.filter(is_active=True))
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 4, "class": "input"}))
    channels = forms.MultipleChoiceField(
        choices=[("sms", "SMS"), ("email", "Email")],
        widget=forms.CheckboxSelectMultiple,
        initial=["email"],
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["team"].widget.attrs["class"] = "input"
        if user and not user.is_staff:
            self.fields["team"].queryset = Team.objects.filter(leaders=user, is_active=True)


def rsvp_response(request, token, accept):
    try:
        data = verify_rsvp_token(token)
        assignment = get_object_or_404(Assignment, pk=data["assignment_id"])
    except Exception:
        return render(
            request,
            "communications/rsvp_result.html",
            {"error": "Invalid or expired link."},
        )

    rsvp = record_rsvp(assignment, accept=accept)

    return render(
        request,
        "communications/rsvp_result.html",
        {
            "assignment": assignment,
            "accepted": accept,
            "rsvp": rsvp,
        },
    )


def rsvp_accept(request, token):
    return rsvp_response(request, token, accept=True)


def rsvp_decline(request, token):
    return rsvp_response(request, token, accept=False)


@login_required
@user_passes_test(is_leader_or_staff)
def mass_message(request):
    if request.method == "POST":
        form = MassMessageForm(request.POST, user=request.user)
        if form.is_valid():
            channels = form.cleaned_data["channels"]
            send_mass_message.delay(
                team_id=form.cleaned_data["team"].pk,
                message=form.cleaned_data["message"],
                channels=channels,
                sender_user_id=request.user.pk,
            )
            if request.htmx:
                return render(request, "communications/partials/mass_message_sent.html")
            return redirect("communications:mass_message")
    else:
        form = MassMessageForm(user=request.user)
    return render(request, "communications/mass_message.html", {"form": form})
