from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("events/<slug:slug>/", views.event_detail, name="event-detail"),
    path("events/<slug:slug>/register/", views.register_for_event, name="register-event"),
    path("accounts/signup/", views.signup, name="signup"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="events/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("my-registrations/", views.my_registrations, name="my-registrations"),
    path(
        "my-registrations/<int:registration_id>/cancel/",
        views.cancel_registration,
        name="cancel-registration",
    ),
]
