from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .api_views import (
    EventViewSet,
    RegistrationViewSet,
    SessionLoginView,
    SessionLogoutView,
    SignUpView,
)

router = DefaultRouter()
router.register("events", EventViewSet, basename="event")
router.register("registrations", RegistrationViewSet, basename="registration")

urlpatterns = [
    path("auth/register/", SignUpView.as_view(), name="api-register"),
    path("auth/login/", SessionLoginView.as_view(), name="api-login"),
    path("auth/logout/", SessionLogoutView.as_view(), name="api-logout"),
    path("", include(router.urls)),
]
