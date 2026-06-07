
from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .models import Campus, ServiceTime


def is_leader_or_staff(user):
    return user.is_staff or user.is_team_leader()


class CampusForm(forms.ModelForm):
    class Meta:
        model = Campus
        fields = ["name", "address", "is_active"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2, "class": "input"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "input")


class ServiceTimeForm(forms.ModelForm):
    class Meta:
        model = ServiceTime
        fields = ["campus", "name", "weekday", "start_time", "duration_minutes", "is_active"]
        widgets = {"start_time": forms.TimeInput(attrs={"type": "time", "class": "input"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "start_time":
                field.widget.attrs.setdefault("class", "input")


@login_required
@user_passes_test(is_leader_or_staff)
def campus_list(request):
    campuses = Campus.objects.prefetch_related("service_times")
    return render(request, "campuses/campus_list.html", {"campuses": campuses})


@login_required
@user_passes_test(is_leader_or_staff)
def campus_create(request):
    if request.method == "POST":
        form = CampusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("campuses:list")
    else:
        form = CampusForm()
    return render(request, "campuses/campus_form.html", {"form": form, "title": "Add Campus"})


@login_required
@user_passes_test(is_leader_or_staff)
def campus_edit(request, pk):
    campus = get_object_or_404(Campus, pk=pk)
    if request.method == "POST":
        form = CampusForm(request.POST, instance=campus)
        if form.is_valid():
            form.save()
            return redirect("campuses:list")
    else:
        form = CampusForm(instance=campus)
    return render(request, "campuses/campus_form.html", {"form": form, "title": "Edit Campus"})


@login_required
@user_passes_test(is_leader_or_staff)
def service_time_create(request):
    if request.method == "POST":
        form = ServiceTimeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("campuses:list")
    else:
        initial = {}
        if campus_id := request.GET.get("campus"):
            initial["campus"] = campus_id
        form = ServiceTimeForm(initial=initial)
    return render(
        request,
        "campuses/service_time_form.html",
        {"form": form, "title": "Add Service Time"},
    )


@login_required
@user_passes_test(is_leader_or_staff)
def service_time_edit(request, pk):
    service_time = get_object_or_404(ServiceTime, pk=pk)
    if request.method == "POST":
        form = ServiceTimeForm(request.POST, instance=service_time)
        if form.is_valid():
            form.save()
            return redirect("campuses:list")
    else:
        form = ServiceTimeForm(instance=service_time)
    return render(
        request,
        "campuses/service_time_form.html",
        {"form": form, "title": "Edit Service Time"},
    )
