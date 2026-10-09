from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Event, EventRegistration
from .services import RegistrationError, register_user_for_event


class EventSerializer(serializers.ModelSerializer):
    spots_remaining = serializers.IntegerField(read_only=True)
    registration_open = serializers.BooleanField(
        source="is_registration_open", read_only=True
    )

    class Meta:
        model = Event
        fields = (
            "id", "title", "slug", "summary", "description", "category",
            "location", "starts_at", "ends_at", "capacity", "spots_remaining",
            "registration_open", "image_url",
        )


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = get_user_model()
        fields = ("id", "username", "email", "first_name", "password")
        read_only_fields = ("id",)

    def validate_email(self, value):
        email = value.strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)


class RegistrationSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(), source="event", write_only=True
    )

    class Meta:
        model = EventRegistration
        fields = (
            "id", "event", "event_id", "status", "created_at", "cancelled_at"
        )
        read_only_fields = ("id", "status", "created_at", "cancelled_at")

    def create(self, validated_data):
        user = self.context["request"].user
        try:
            return register_user_for_event(validated_data["event"], user)
        except RegistrationError as exc:
            raise serializers.ValidationError({"event_id": str(exc)}) from exc
