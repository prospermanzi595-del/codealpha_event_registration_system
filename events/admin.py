from django.contrib import admin

from .models import Event, EventRegistration


class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    readonly_fields = ("user", "status", "created_at", "cancelled_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title", "category", "starts_at", "location", "status", "capacity",
        "confirmed_count",
    )
    list_filter = ("status", "category", "starts_at")
    search_fields = ("title", "summary", "description", "location")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [EventRegistrationInline]

    @admin.display(description="Confirmed")
    def confirmed_count(self, obj):
        return obj.registrations.filter(status=EventRegistration.Status.CONFIRMED).count()


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ("event", "user", "status", "created_at", "cancelled_at")
    list_filter = ("status", "event")
    search_fields = ("event__title", "user__username", "user__email")
    readonly_fields = ("created_at", "cancelled_at")
