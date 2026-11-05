import sys
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, get_connection
from django.conf import settings

class Command(BaseCommand):
    help = "Tests Gmail SMTP email connection and diagnoses any issues"

    def handle(self, *args, **options):
        self.stdout.write("=== Testing Email Configuration ===")
        user = settings.EMAIL_HOST_USER
        pwd = settings.EMAIL_HOST_PASSWORD or ""
        masked_pwd = (pwd[:2] + "*" * (len(pwd) - 4) + pwd[-2:]) if len(pwd) > 4 else "***"
        self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"EMAIL_HOST_USER: {user}")
        self.stdout.write(f"EMAIL_HOST_PASSWORD: {masked_pwd} (Length: {len(pwd)})")
        self.stdout.write(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"EMAIL_TIMEOUT: {getattr(settings, 'EMAIL_TIMEOUT', None)}")

        # Test standard settings (Port 587 TLS)
        self.stdout.write("\nAttempting to send test email via Port 587 (TLS)...")
        try:
            conn = get_connection(
                host=settings.EMAIL_HOST,
                port=587,
                username=user,
                password=pwd,
                use_tls=True,
                use_ssl=False,
                timeout=10
            )
            res = send_mail(
                subject="CraftyKids Email Test (Port 587)",
                message="Congratulations! Your CraftyKids automated email system is working perfectly!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user],
                connection=conn,
                fail_silently=False
            )
            self.stdout.write(self.style.SUCCESS(f"SUCCESS! Test email sent via Port 587 to {user}."))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Port 587 FAILED: {type(e).__name__} -> {e}"))

        # Test fallback Port 465 SSL
        self.stdout.write("\nAttempting fallback via Port 465 (SSL)...")
        try:
            conn = get_connection(
                host=settings.EMAIL_HOST,
                port=465,
                username=user,
                password=pwd,
                use_tls=False,
                use_ssl=True,
                timeout=10
            )
            res = send_mail(
                subject="CraftyKids Email Test (Port 465)",
                message="Congratulations! Your CraftyKids automated email system is working on Port 465!",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user],
                connection=conn,
                fail_silently=False
            )
            self.stdout.write(self.style.SUCCESS(f"SUCCESS! Test email sent via Port 465 to {user}."))
            self.stdout.write("NOTE: You should switch settings.py to port 465 (SSL) for best reliability on Railway!")
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Port 465 FAILED: {type(e).__name__} -> {e}"))

        self.stdout.write(self.style.ERROR("\nDiagnosis Complete: Both ports failed. See errors above."))
