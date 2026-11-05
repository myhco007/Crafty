import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from main.email_utils import send_via_brevo, get_email_template

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

        website_url = "https://crafty-production-76d7.up.railway.app"

        text_body, html_body = get_email_template(
            title="Registration Received Successfully",
            greeting_name="Crafty Explorer",
            body_paragraphs=[
                "Thank you for registering with Crafty Kids!",
                f"This email confirms that your Gmail address ({recipient}) has been successfully used to register a new account on our platform.",
                "For the safety and security of our students, all new accounts require review and approval by the Main Admin before you can log in. We will send you an email confirmation as soon as your account is approved."
            ],
            detail_rows=[
                ("Registered Email", recipient),
                ("Username", "test_user"),
                ("Account Role", "Student"),
                ("Account Status", "Pending Admin Approval")
            ],
            button_text="Visit Crafty Kids Platform",
            button_url=website_url
        )

        success = send_via_brevo(
            subject="Welcome to Crafty Kids - Registration Received",
            message=text_body,
            recipient_list=[recipient],
            html_content=html_body
        )

        if success:
            self.stdout.write(self.style.SUCCESS(f"\n SUCCESS! Professional test email was accepted by Brevo for delivery to {recipient}!"))
            self.stdout.write(self.style.SUCCESS("Check your Gmail inbox on your phone or computer."))
        else:
            self.stdout.write(self.style.ERROR("\n❌ FAILED! Brevo API key may not be set or lacks permissions."))
