# app/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_otp_email(self, email, otp):
    """
    Send login OTP to user email.
    """
    subject = 'AnkuOn2 — Your Login OTP'
    message = (
        f'Your AnkuOn2 verification code is: {otp}\n\n'
        f'This code is valid for a short time. Do not share it with anyone.\n\n'
        f'If you did not request this, ignore this email.\n\n'
        f'— AnkuOn2'
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or settings.EMAIL_HOST_USER

    try:
        sent = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            fail_silently=False,
        )
        print(f'[OTP EMAIL] sent={sent} to={email}')
        return {'ok': True, 'email': email}
    except Exception as exc:
        print(f'[OTP EMAIL ERROR] {email}: {exc}')
        # Still print OTP so local testing never blocks
        print(f'[DEMO OTP] {email}: {otp}')
        try:
            raise self.retry(exc=exc)
        except Exception:
            return {'ok': False, 'error': str(exc)}
