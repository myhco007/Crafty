import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from main.email_utils import send_via_brevo

class Command(BaseCommand):
    help = "Tests Brevo HTTPS email delivery and verifies email configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            dest='recipient',
            default='johnsentasis01@gmail.com',
            help='Recipient email address to test delivery'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']
        self.stdout.write("=== Testing Brevo HTTPS Email Delivery ===")
        self.stdout.write(f"Recipient: {recipient}")
        self.stdout.write("Sending via Brevo HTTPS API (Port 443)...")

        success = send_via_brevo(
            subject="CraftyKids System: Email Delivery Verified! 🚀",
            message=(
                f"Hello!\n\n"
                f"This is an automated test from Crafty Kids Capstone System running on Railway.\n"
                f"If you are reading this email, Brevo HTTPS delivery is working 100% and will deliver to ANY valid Gmail address!\n\n"
                f"- Crafty Kids System"
            ),
            recipient_list=[recipient]
        )

        if success:
            self.stdout.write(self.style.SUCCESS(f"\n🎉 SUCCESS! Test email was successfully accepted by Brevo for delivery to {recipient}!"))
            self.stdout.write(self.style.SUCCESS("Check your Gmail inbox (and Spam/Junk folder just in case)."))
        else:
            self.stdout.write(self.style.ERROR("\n❌ FAILED! Brevo API key may not be set or lacks permissions."))
