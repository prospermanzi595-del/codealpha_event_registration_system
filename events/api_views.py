from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Event, EventRegistration
from .serializers import EventSerializer, RegistrationSerializer, SignUpSerializer


class EventViewSet(ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "head", "options"]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Event.objects.filter(
            status=Event.Status.PUBLISHED, starts_at__gt=timezone.now()
        )
        search = self.request.query_params.get("search")
        category = self.request.query_params.get("category")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(summary__icontains=search)
                | Q(description__icontains=search)
                | Q(location__icontains=search)
            )
        if category:
            queryset = queryset.filter(category__iexact=category)
        return queryset


class SignUpView(generics.CreateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(
            {
                "id": user.pk,
                "username": user.get_username(),
                "email": user.email,
                "detail": "Account created and signed in.",
            },
            status=status.HTTP_201_CREATED,
        )


class SessionLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @method_decorator(csrf_protect)
    def post(self, request):
        identity = request.data.get("username") or request.data.get("email")
        password = request.data.get("password")
        if not identity or not password:
            return Response(
                {"detail": "Enter your username or email and password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        username = identity
        if "@" in identity:
            from django.contrib.auth import get_user_model

            user = get_user_model().objects.filter(email__iexact=identity).first()
            username = user.get_username() if user else identity
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"detail": "The supplied credentials are invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response({"detail": "Signed in.", "username": user.get_username()})


class SessionLogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegistrationViewSet(ModelViewSet):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        return EventRegistration.objects.filter(user=self.request.user).select_related(
            "event"
        )

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        registration = self.get_object()
        if registration.status == EventRegistration.Status.CANCELLED:
            return Response(
                {"detail": "This registration is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        registration.status = EventRegistration.Status.CANCELLED
        registration.cancelled_at = timezone.now()
        registration.save(update_fields=["status", "cancelled_at"])
        return Response(self.get_serializer(registration).data)
