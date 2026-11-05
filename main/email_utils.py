import threading
from django.core.mail import send_mail
from django.conf import settings

def send_mail_async(subject, message, recipient_list, from_email=None, fail_silently=True):
    """
    Sends an email asynchronously in a background thread so the HTTP request
    never hangs or times out even if SMTP is slow or unreachable.
    """
    sender = from_email or settings.DEFAULT_FROM_EMAIL
    recipients = [recipient_list] if isinstance(recipient_list, str) else list(recipient_list)

    def _worker():
        try:
            send_mail(subject, message, sender, recipients, fail_silently=fail_silently)
            print(f"[Email Worker] Sent email '{subject}' to {recipients}")
        except Exception as e:
            print(f"[Email Worker ERROR] Could not send email '{subject}' to {recipients}: {e}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
