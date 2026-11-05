import json
import os
import threading
import urllib.request
from django.conf import settings
from django.core.mail import send_mail

BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '').strip()
BREVO_SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL', 'myhcobaling@gmail.com')

def send_via_brevo(subject, message, recipient_list, from_email=None, html_content=None):
    api_key = BREVO_API_KEY or getattr(settings, 'BREVO_API_KEY', '')
    if not api_key:
        return False
    recipients = [recipient_list] if isinstance(recipient_list, str) else list(recipient_list)
    sender_email = from_email or BREVO_SENDER_EMAIL or getattr(settings, 'DEFAULT_FROM_EMAIL', 'myhcobaling@gmail.com')

    payload = {
        'sender': {'name': 'Crafty Kids', 'email': sender_email},
        'to': [{'email': r} for r in recipients],
        'subject': subject,
        'textContent': message,
    }
    if html_content:
        payload['htmlContent'] = html_content

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
def send_via_resend(subject, message, recipient_list, from_email=None, html_content=None):
    return send_via_brevo(subject, message, recipient_list, from_email, html_content)

def send_mail_async(subject, message, recipient_list, from_email=None, html_message=None, fail_silently=True):
    sender = from_email or settings.DEFAULT_FROM_EMAIL
    recipients = [recipient_list] if isinstance(recipient_list, str) else list(recipient_list)

    print(f"\n==========================================")
    print(f"[OUTGOING EMAIL] To: {recipients}")
    print(f"Subject: {subject}")
    print(f"==========================================\n")

    # 1. Primary: Brevo HTTPS API (fast ~0.5s HTTP call, 100% reliable on cloud)
    try:
        if send_via_brevo(subject, message, recipients, sender, html_content=html_message):
            print(f"[Email Success] Sent to {recipients} via Brevo HTTPS")
            return None
    except Exception as e:
        print(f"[Brevo Direct Exception] {e}")

    # 2. Fallback in background thread for SMTP
    def _worker():
        try:
            send_mail(
                subject,
                message,
                sender,
                recipients,
                fail_silently=fail_silently,
                html_message=html_message
            )
            print(f"[SMTP Fallback] Sent email '{subject}' to {recipients}")
        except Exception as e:
            print(f"[SMTP Fallback Notice] Could not send via SMTP ({e})")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread

def get_email_template(title, greeting_name, body_paragraphs, detail_rows=None, button_text=None, button_url=None):
    """
    Returns (text_content, html_content) with clean styling and professional branding.
    """
    text_lines = [f"Hello {greeting_name},", ""]
    for p in body_paragraphs:
        text_lines.append(p)
        text_lines.append("")

    if detail_rows:
        text_lines.append("Account Details:")
        for label, val in detail_rows:
            text_lines.append(f"- {label}: {val}")
        text_lines.append("")

    if button_url:
        text_lines.append(f"Website Link: {button_url}")
        text_lines.append("")

    text_lines.append("Thank you,")
    text_lines.append("Crafty Kids Team")
    text_content = "\n".join(text_lines)

    # HTML Version
    details_html = ""
    if detail_rows:
        rows_str = "".join([
            f"""<tr>
                <td style="padding: 8px 12px; font-weight: bold; color: #374151; border-bottom: 1px solid #e5e7eb;">{label}</td>
                <td style="padding: 8px 12px; color: #111827; border-bottom: 1px solid #e5e7eb;">{val}</td>
            </tr>""" for label, val in detail_rows
        ])
        details_html = f"""
        <table style="width: 100%; margin: 20px 0; border-collapse: collapse; background-color: #f9fafb; border-radius: 8px; overflow: hidden; border: 1px solid #e5e7eb; font-size: 14px;">
            <tbody>
                {rows_str}
            </tbody>
        </table>
        """

    button_html = ""
    if button_url and button_text:
        button_html = f"""
        <div style="text-align: center; margin: 30px 0;">
            <a href="{button_url}" style="background: linear-gradient(135deg, #16a34a, #15803d); color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 4px 6px rgba(22, 163, 74, 0.25);">
                {button_text} &rarr;
            </a>
            <p style="margin-top: 10px; font-size: 12px; color: #6b7280;">Or copy this link: <a href="{button_url}" style="color: #16a34a;">{button_url}</a></p>
        </div>
        """

    paragraphs_html = "".join([f"<p style='margin: 0 0 14px 0; line-height: 1.6; color: #374151; font-size: 15px;'>{p}</p>" for p in body_paragraphs])

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
<table border="0" cellpadding="0" cellspacing="0" width="100%" style="padding: 30px 15px;">
    <tr>
        <td align="center">
            <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 580px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.06); border: 1px solid #e5e7eb;">
                <!-- Header -->
                <tr>
                    <td style="background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); padding: 25px 30px; text-align: center;">
                        <h1 style="margin: 0; color: #ffffff; font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">🎨 Crafty Kids</h1>
                        <p style="margin: 5px 0 0; color: #dcfce7; font-size: 14px; font-weight: 500;">Interactive Learning & Capstone Platform</p>
                    </td>
                </tr>
                <!-- Body -->
                <tr>
                    <td style="padding: 30px 30px 20px;">
                        <h2 style="margin: 0 0 16px; color: #111827; font-size: 20px; font-weight: 700;">{title}</h2>
                        <p style="margin: 0 0 16px; color: #374151; font-size: 15px; font-weight: 600;">Hello {greeting_name},</p>
                        {paragraphs_html}
                        {details_html}
                        {button_html}
                    </td>
                </tr>
                <!-- Footer -->
                <tr>
                    <td style="padding: 20px 30px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; text-align: center; color: #6b7280; font-size: 12px; line-height: 1.5;">
                        <p style="margin: 0 0 6px;">This is an automated notification from <strong>Crafty Kids</strong>.</p>
                        <p style="margin: 0;">If you did not register this account or have questions, please disregard this email.</p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>"""

    return text_content, html_content
