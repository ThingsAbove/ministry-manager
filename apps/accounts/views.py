from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, RegisterForm, VolunteerProfileForm


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("core:dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    profile_obj = request.user.volunteer_profile
    if request.method == "POST":
        form = VolunteerProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            if request.htmx:
                return render(
                    request,
                    "accounts/partials/profile_form.html",
                    {"form": VolunteerProfileForm(instance=profile_obj), "saved": True},
                )
            return redirect("accounts:profile")
    else:
        form = VolunteerProfileForm(instance=profile_obj)

    context = {"form": form}
    template = (
        "accounts/partials/profile_form.html"
        if request.htmx and request.method == "GET" and request.GET.get("partial")
        else "accounts/profile.html"
    )
    return render(request, template, context)
