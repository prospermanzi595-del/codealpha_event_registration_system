from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event


class Command(BaseCommand):
    help = "Create a small set of upcoming CodeAlpha demo events."

    def handle(self, *args, **options):
        now = timezone.now()
        examples = [
            {
                "title": "The Next Big Idea",
                "summary": "An evening of bold ideas, honest stories, and new connections.",
                "description": (
                    "Meet the people building what comes next. Hear short, lively "
                    "talks from local founders and makers, then stay for conversation "
                    "and new connections."
                ),
                "category": "Community",
                "location": "Accra, Ghana",
                "starts_at": now + timedelta(days=14),
                "ends_at": now + timedelta(days=14, hours=3),
                "capacity": 80,
            },
            {
                "title": "Build Night: Creative Coding",
                "summary": "Bring a laptop, try something new, and make it together.",
                "description": (
                    "A welcoming hands-on workshop for curious beginners and "
                    "experienced creatives alike. Come ready to experiment."
                ),
                "category": "Technology",
                "location": "CodeAlpha Studio, Accra",
                "starts_at": now + timedelta(days=21),
                "ends_at": now + timedelta(days=21, hours=2),
                "capacity": 40,
            },
            {
                "title": "Sunday Social Club",
                "summary": "Good coffee, easy conversation, and a slower kind of Sunday.",
                "description": (
                    "Make room for a relaxed afternoon with neighbors, new friends, "
                    "great coffee, and a little live music."
                ),
                "category": "Social",
                "location": "Osu, Accra",
                "starts_at": now + timedelta(days=28),
                "ends_at": now + timedelta(days=28, hours=2),
                "capacity": None,
            },
        ]
        created_count = 0
        for example in examples:
            _, created = Event.objects.update_or_create(
                title=example["title"],
                defaults={
                    **example,
                    "status": Event.Status.PUBLISHED,
                },
            )
            created_count += int(created)
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo events ready; created {created_count} new event(s)."
            )
        )
