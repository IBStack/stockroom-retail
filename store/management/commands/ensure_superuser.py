import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or update the configured deployment superuser without storing credentials in source control."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
        if not username or not password:
            self.stdout.write("Superuser bootstrap skipped: deployment credentials are not configured.")
            return
        User = get_user_model()
        user, _ = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Deployment superuser is ready: {username}"))
