from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import SignUpForm
from .models import Event, EventRegistration
from .services import RegistrationError, register_user_for_event


@ensure_csrf_cookie
def home(request):
    events = Event.objects.filter(
        status=Event.Status.PUBLISHED, starts_at__gt=timezone.now()
    )[:6]
    return render(request, "events/home.html", {"events": events})


@ensure_csrf_cookie
def event_detail(request, slug):
    event = get_object_or_404(
        Event, slug=slug, status=Event.Status.PUBLISHED, starts_at__gt=timezone.now()
    )
    is_registered = request.user.is_authenticated and EventRegistration.objects.filter(
        event=event, user=request.user, status=EventRegistration.Status.CONFIRMED
    ).exists()
    return render(
        request, "events/event_detail.html",
        {"event": event, "is_registered": is_registered},
    )


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready. Welcome to the community.")
        next_url = request.GET.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect("home")
    return render(request, "events/signup.html", {"form": form})


@login_required
def register_for_event(request, slug):
    if request.method != "POST":
        return redirect("event-detail", slug=slug)
    event = get_object_or_404(Event, slug=slug)
    try:
        register_user_for_event(event, request.user)
        messages.success(request, "Your spot is confirmed. See you there!")
    except RegistrationError as exc:
        messages.error(request, str(exc))
    return redirect("my-registrations")


@login_required
def my_registrations(request):
    registrations = request.user.event_registrations.select_related("event")
    return render(
        request, "events/my_registrations.html", {"registrations": registrations}
    )


@login_required
def cancel_registration(request, registration_id):
    if request.method != "POST":
        return redirect("my-registrations")
    registration = get_object_or_404(
        EventRegistration, pk=registration_id, user=request.user
    )
    if registration.status == EventRegistration.Status.CONFIRMED:
        with transaction.atomic():
            registration = EventRegistration.objects.select_for_update().get(
                pk=registration.pk
            )
            if registration.status == EventRegistration.Status.CONFIRMED:
                registration.status = EventRegistration.Status.CANCELLED
                registration.cancelled_at = timezone.now()
                registration.save(update_fields=["status", "cancelled_at"])
                messages.success(request, "Your registration has been cancelled.")
    return redirect("my-registrations")
