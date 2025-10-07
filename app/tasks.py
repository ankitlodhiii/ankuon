# app/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_otp_email(email, otp):
    send_mail(
        subject='AnkuOn OTP Verification',
        message=f'Your OTP is {otp}. Valid for 5 minutes.',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
