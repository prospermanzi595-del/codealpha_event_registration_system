from django.db import transaction
from django.utils import timezone

from .models import Event, EventRegistration


class RegistrationError(Exception):
    pass


@transaction.atomic
def register_user_for_event(event, user):
    event = Event.objects.select_for_update().get(pk=event.pk)
    if event.status != Event.Status.PUBLISHED:
        raise RegistrationError("This event is not open for registration.")
    if event.starts_at <= timezone.now():
        raise RegistrationError("Registration has closed for this event.")

    registration = EventRegistration.objects.filter(event=event, user=user).first()
    if registration and registration.status == EventRegistration.Status.CONFIRMED:
        raise RegistrationError("You are already registered for this event.")
    active_count = event.registrations.filter(
        status=EventRegistration.Status.CONFIRMED
    ).count()
    if event.capacity is not None and active_count >= event.capacity:
        raise RegistrationError("Sorry, this event has reached capacity.")

    if registration:
        registration.status = EventRegistration.Status.CONFIRMED
        registration.cancelled_at = None
        registration.save(update_fields=["status", "cancelled_at"])
        return registration
    return EventRegistration.objects.create(event=event, user=user)
