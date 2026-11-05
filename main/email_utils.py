import json
import os
import threading
import urllib.request
from django.conf import settings
from django.core.mail import send_mail

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')

def send_via_resend(subject, message, recipient_list, from_email=None):
    api_key = RESEND_API_KEY or getattr(settings, 'RESEND_API_KEY', '')
    if not api_key:
        return False
    recipients = [recipient_list] if isinstance(recipient_list, str) else list(recipient_list)
    payload = {
        'from': 'CraftyKids <onboarding@resend.dev>',
        'to': recipients,
        'subject': subject,
        'text': message,
    }
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'CraftyKids/1.0',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[Resend API] SUCCESS delivering '{subject}' to {recipients}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='ignore')
        print(f"[Resend API Notice] {e.code}: {error_body}")
        return False
    except Exception as e:
        print(f"[Resend API Exception] {e}")
        return False

def send_mail_async(subject, message, recipient_list, from_email=None, fail_silently=True):
    sender = from_email or settings.DEFAULT_FROM_EMAIL
    recipients = [recipient_list] if isinstance(recipient_list, str) else list(recipient_list)

    # Always log the full notification to the console for easy monitoring in Railway logs
    print(f"\n==========================================")
    print(f"[OUTGOING EMAIL] To: {recipients}")
    print(f"Subject: {subject}")
    print(f"Message:\n{message}")
    print(f"==========================================\n")

    def _worker():
        # First attempt: Resend HTTPS API (Port 443, never blocked by cloud firewalls)
        if send_via_resend(subject, message, recipients, sender):
            return

        # Fallback attempt: Standard SMTP if reachable
        try:
            send_mail(subject, message, sender, recipients, fail_silently=fail_silently)
            print(f"[SMTP Fallback] Sent email '{subject}' to {recipients}")
        except Exception as e:
            print(f"[SMTP Fallback Notice] Could not send via SMTP ({e})")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
