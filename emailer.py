import os
import resend
from config import RECEIVER_EMAIL

resend.api_key = os.getenv("RESEND_API_KEY")
EMAIL_FROM = "WebDev Lead Bot <onboarding@resend.dev>"


def send_email(html_body, lead_count=0, date_str=""):
    subject = f"🌍 {lead_count} WebDev Lead(s) From USA/UK/Canada/AU – {date_str}"
    try:
        params = {
            "from": EMAIL_FROM,
            "to": [RECEIVER_EMAIL],
            "subject": subject,
            "html": html_body,
        }
        email = resend.Emails.send(params)
        print(f"[INFO] Email sent successfully. ID: {email['id']}")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        raise
