from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Event, EventRegistration


class EventRegistrationTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.user = get_user_model().objects.create_user(
            username="attendee", email="attendee@example.com", password="StrongPass123!"
        )
        self.event = Event.objects.create(
            title="Community Tech Night",
            summary="A friendly evening for builders.",
            description="Talks and networking.",
            category="Technology",
            location="Accra",
            starts_at=timezone.now() + timedelta(days=10),
            ends_at=timezone.now() + timedelta(days=10, hours=2),
            capacity=1,
            status=Event.Status.PUBLISHED,
        )

    def test_public_event_list_hides_drafts_and_past_events(self):
        Event.objects.create(
            title="Private draft",
            summary="Not public.",
            description="Not public.",
            category="Community",
            location="Accra",
            starts_at=timezone.now() + timedelta(days=2),
            ends_at=timezone.now() + timedelta(days=2, hours=1),
        )
        response = self.client_api.get("/api/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.event.slug)

    def test_authenticated_user_can_register_and_cancel(self):
        self.client_api.force_authenticate(self.user)
        response = self.client_api.post(
            "/api/registrations/", {"event_id": self.event.pk}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        registration_id = response.data["id"]

        cancelled = self.client_api.post(
            f"/api/registrations/{registration_id}/cancel/", {}, format="json"
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.data["status"], EventRegistration.Status.CANCELLED)

    def test_cancelled_attendee_can_register_again(self):
        registration = EventRegistration.objects.create(
            event=self.event,
            user=self.user,
            status=EventRegistration.Status.CANCELLED,
            cancelled_at=timezone.now(),
        )
        self.client_api.force_authenticate(self.user)
        response = self.client_api.post(
            "/api/registrations/", {"event_id": self.event.pk}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["id"], registration.pk)
        self.assertEqual(response.data["status"], EventRegistration.Status.CONFIRMED)

    def test_event_capacity_is_enforced(self):
        first = EventRegistration.objects.create(event=self.event, user=self.user)
        other_user = get_user_model().objects.create_user(
            username="another", password="StrongPass123!"
        )
        self.client_api.force_authenticate(other_user)
        response = self.client_api.post(
            "/api/registrations/", {"event_id": self.event.pk}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            EventRegistration.objects.filter(pk=first.pk).exists()
        )
        self.assertFalse(
            EventRegistration.objects.filter(event=self.event, user=other_user).exists()
        )

    def test_registrations_are_private_to_the_signed_in_user(self):
        registration = EventRegistration.objects.create(event=self.event, user=self.user)
        other_user = get_user_model().objects.create_user(
            username="another", password="StrongPass123!"
        )
        self.client_api.force_authenticate(other_user)
        response = self.client_api.get(f"/api/registrations/{registration.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_web_event_page_and_protected_cancellation(self):
        response = self.client.get(reverse("event-detail", args=[self.event.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)
        registration = EventRegistration.objects.create(event=self.event, user=self.user)
        other_user = get_user_model().objects.create_user(
            username="another", password="StrongPass123!"
        )
        self.client.force_login(other_user)
        response = self.client.post(
            reverse("cancel-registration", args=[registration.pk])
        )
        self.assertEqual(response.status_code, 404)
        registration.refresh_from_db()
        self.assertEqual(registration.status, EventRegistration.Status.CONFIRMED)

    def test_csrf_cookie_is_available_for_same_origin_api_clients(self):
        response = self.client.get("/")
        self.assertIn("csrftoken", response.cookies)

    def test_api_login_requires_csrf_and_accepts_email(self):
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

        client.get("/")
        csrf_token = client.cookies["csrftoken"].value
        response = client.post(
            "/api/auth/login/",
            {"email": self.user.email, "password": "StrongPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, 200)
