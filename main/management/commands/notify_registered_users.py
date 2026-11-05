import time
import re
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.email_utils import send_via_brevo, get_email_template

# Obvious test patterns to avoid hard bounces on Brevo free tier
FAKE_PATTERNS = [
    r'^admin@example\.com$',
    r'.*@gmai\.com$',
    r'^[0-9]+@gmail\.com$',
    r'^(asdf|asda|qwer|zxcv|dummy)[0-9a-z]*@gmail\.com$',
    r'.*(asdasd|qweqwr|sgaq2234).*@gmail\.com$',
    r'^(student|teacher|teachear|test|testteacher)@gmail\.com$',
]

def is_likely_fake(email):
    email = email.strip().lower()
    for pattern in FAKE_PATTERNS:
        if re.match(pattern, email):
            return True
    return False

class Command(BaseCommand):
    help = "Sends the professional registration notification email to registered users"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate sending without actually emailing'
        )
        parser.add_argument(
            '--username',
            type=str,
            default='',
            help='Send only to a specific username'
        )
        parser.add_argument(
            '--include-test-accounts',
            action='store_true',
            help='Include obvious test/gibberish accounts that might hard-bounce'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        target_username = options['username']
        include_tests = options['include_test_accounts']

        website_url = "https://crafty-production-76d7.up.railway.app"

        qs = User.objects.filter(is_active=True).exclude(email='').order_by('id')
        if target_username:
            qs = qs.filter(username=target_username)

        users = list(qs)
        self.stdout.write(f"=== Found {len(users)} registered active users with email ===")

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for user in users:
            email = (user.email or '').strip()
            if not email or '@' not in email:
                skipped_count += 1
                continue

            if not include_tests and is_likely_fake(email):
                self.stdout.write(self.style.WARNING(f"[SKIP] Skipping test/dummy email: {user.username} ({email})"))
                skipped_count += 1
                continue

            full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            role_name = "Teacher / Educator" if (user.is_staff or getattr(user.profile, 'is_teacher', False) if hasattr(user, 'profile') else False) else "Student"
            
            # Check approval status
            is_approved = getattr(user.profile, 'is_approved', True) if hasattr(user, 'profile') else True
            status_text = "Active & Approved" if is_approved else "Pending Admin Approval"

            title = "Welcome to Crafty Kids!" if is_approved else "Registration Received Successfully!"
            subject = f"Your Crafty Kids Account - {status_text}"

            paragraphs = [
                f"Thank you for being part of Crafty Kids!",
                f"This email confirms that your Gmail address ({email}) is registered on our learning platform with the username: <strong>{user.username}</strong>.",
                f"You can access all interactive lessons, quizzes, crafts, and videos directly through the official website link below."
            ]
            if not is_approved:
                paragraphs.append("Your account is currently awaiting review by the Main Admin. You will receive an update once approved.")

            text_body, html_body = get_email_template(
                title=title,
                greeting_name=full_name,
                body_paragraphs=paragraphs,
                detail_rows=[
                    ("Registered Email", email),
                    ("Username", user.username),
                    ("Account Role", role_name),
                    ("Account Status", status_text)
                ],
                button_text="Open Crafty Kids Website",
                button_url=website_url
            )

            if dry_run:
                self.stdout.write(f"[DRY RUN] Would send to: {user.username} <{email}> ({role_name}, {status_text})")
                sent_count += 1
                continue

            self.stdout.write(f"Sending to {user.username} <{email}>...")
            try:
                ok = send_via_brevo(
                    subject=subject,
                    message=text_body,
                    recipient_list=[email],
                    html_content=html_body
                )
                if ok:
                    self.stdout.write(self.style.SUCCESS(f"  [OK] Sent successfully to {email}"))
                    sent_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"  [FAIL] Failed to send to {email}"))
                    failed_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [ERROR] Error sending to {email}: {e}"))
                failed_count += 1

            # Small delay between calls to respect rate limits
            time.sleep(0.5)

        self.stdout.write("\n=== Summary ===")
        self.stdout.write(self.style.SUCCESS(f"Sent: {sent_count}"))
        self.stdout.write(f"Skipped dummy/fake: {skipped_count}")
        if failed_count:
            self.stdout.write(self.style.ERROR(f"Failed: {failed_count}"))
