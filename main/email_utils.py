import json
import os
import threading
import urllib.request
from django.conf import settings
from django.core.mail import send_mail

BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', 'myhcobaling@gmail.com')

def send_via_brevo(subject, message, recipient_list, from_email=None):
    api_key = BREVO_API_KEY or getattr(settings, 'BREVO_API_KEY', '')
    if not api_key:
        return False
    recipients = [recipient_list] if isinstance(recipient_list, str) else list(recipient_list)
    sender_email = from_email or BREVO_SENDER_EMAIL or getattr(settings, 'DEFAULT_FROM_EMAIL', 'myhcobaling@gmail.com')

    payload = {
        'sender': {'name': 'CraftyKids', 'email': sender_email},
        'to': [{'email': r} for r in recipients],
        'subject': subject,
        'textContent': message,
    }
    req = urllib.request.Request(
        'https://api.brevo.com/v3/smtp/email',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'api-key': api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'CraftyKids/1.0',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[Brevo API] SUCCESS delivering '{subject}' to {recipients} (Status: {resp.status})")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        print(f"[Brevo API Error] {e.code}: {error_body}")
        return False
    except Exception as e:
        print(f"[Brevo API Exception] {e}")
        return False

# Backwards compatibility alias
def send_via_resend(subject, message, recipient_list, from_email=None):
    return send_via_brevo(subject, message, recipient_list, from_email)

def send_mail_async(subject, message, recipient_list, from_email=None, fail_silently=True):
    sender = from_email or settings.DEFAULT_FROM_EMAIL
    recipients = [recipient_list] if isinstance(recipient_list, str) else list(recipient_list)

    print(f"\n==========================================")
    print(f"[OUTGOING EMAIL] To: {recipients}")
    print(f"Subject: {subject}")
    print(f"Message:\n{message}")
    print(f"==========================================\n")

    def _worker():
        # 1. Primary: Brevo HTTPS API (delivers to ANY Gmail in the world without restrictions)
        if send_via_brevo(subject, message, recipients, sender):
            return

        # 2. Secondary fallback: SMTP
        try:
            send_mail(subject, message, sender, recipients, fail_silently=fail_silently)
            print(f"[SMTP Fallback] Sent email '{subject}' to {recipients}")
        except Exception as e:
            print(f"[SMTP Fallback Notice] Could not send via SMTP ({e})")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
