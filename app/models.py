from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    upi_id = models.CharField(max_length=256, blank=True)
    kyc_status = models.CharField(max_length=20, default='Not Verified')
    otp = models.CharField(max_length=6, blank=True, null=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.email

class Investment(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    returns = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"Investment {self.id} by {self.user.email}"

class Withdrawal(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    requested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    processing_end = models.DateTimeField()
    upi_id = models.CharField(max_length=256)

    def __str__(self):
        return f"Withdrawal {self.id} by {self.user.email}"
