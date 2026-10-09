from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    summary = models.CharField(max_length=280)
    description = models.TextField()
    category = models.CharField(max_length=80, default="Community")
    location = models.CharField(max_length=180)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(
        null=True, blank=True, help_text="Leave empty for unlimited attendance."
    )
    image_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [
            models.Index(fields=["status", "starts_at"]),
            models.Index(fields=["category", "starts_at"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "The end time must be after the start."})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "event"
            candidate = base_slug
            number = 2
            while Event.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{number}"
                number += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def spots_remaining(self):
        if self.capacity is None:
            return None
        return max(self.capacity - self.registrations.filter(
            status=EventRegistration.Status.CONFIRMED
        ).count(), 0)

    @property
    def is_registration_open(self):
        return (
            self.status == self.Status.PUBLISHED
            and self.starts_at > timezone.now()
            and (self.capacity is None or self.spots_remaining > 0)
        )


class EventRegistration(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    event = models.ForeignKey(
        Event, related_name="registrations", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="event_registrations",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"], name="unique_user_registration_per_event"
            ),
        ]
        indexes = [models.Index(fields=["user", "status", "created_at"])]

    def __str__(self):
        return f"{self.user} — {self.event}"
