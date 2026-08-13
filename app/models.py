from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    upi_id = models.CharField(max_length=256, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    kyc_status = models.CharField(max_length=20, default='Not Verified')
    otp = models.CharField(max_length=6, blank=True, null=True)
    verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email


class Kyc(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='kyc')
    pan = models.CharField(max_length=10)
    aadhaar = models.CharField(max_length=12)
    mobile = models.CharField(max_length=15)
    account_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=30, blank=True)
    ifsc = models.CharField(max_length=15, blank=True)
    banks = models.JSONField(default=list, blank=True)  # list of bank dicts
    aadhaar_mobile_linked = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"KYC of {self.user.email}"


class Investment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Pending Bank Transfer', 'Pending Bank Transfer'),
        ('Confirmed', 'Confirmed'),
        ('Failed', 'Failed'),
    ]
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order_id = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, blank=True)  # qr | collect | bank
    virtual_account = models.JSONField(null=True, blank=True)  # VA details
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.order_id} - {self.user.email} - ₹{self.amount}"


class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Rejected', 'Rejected'),
    ]
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='withdrawals')
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    requested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    processing_end = models.DateTimeField()
    bank_account = models.CharField(max_length=30, blank=True)
    ifsc = models.CharField(max_length=15, blank=True)
    account_name = models.CharField(max_length=100, blank=True)
    method = models.CharField(max_length=30, default='NEFT/RTGS/IMPS')
    utr = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Withdrawal {self.id} - {self.user.email}"


class SecurityLog(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='security_logs')
    action = models.CharField(max_length=50)
    detail = models.CharField(max_length=255, blank=True)
    at = models.DateTimeField(auto_now_add=True)
