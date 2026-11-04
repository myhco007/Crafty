from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = "Loads initial datadump.json into the database if empty"

    def handle(self, *args, **options):
        if User.objects.count() == 0:
            if os.path.exists('datadump.json'):
                self.stdout.write("Database has 0 users. Auto-importing datadump.json...")
                call_command('loaddata', 'datadump.json')
                self.stdout.write(self.style.SUCCESS(f"Done! Database now has {User.objects.count()} users."))
            else:
                self.stdout.write("datadump.json not found, skipping.")
        else:
            self.stdout.write(f"Database already populated ({User.objects.count()} users found). Skipping import.")
