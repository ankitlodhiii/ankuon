
from django.db import models
from django.contrib.auth.models import User


# =====================================================
# USER PROFILE
# =====================================================

class UserProfile(models.Model):
    KYC_STATUS = [
        ("Pending", "Pending"),
        ("Verified", "Verified"),
        ("Rejected", "Rejected"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150, blank=True)
    upi = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    kyc_status = models.CharField(
        max_length=20,
        choices=KYC_STATUS,
        default="Pending"
    )
    otp = models.CharField(max_length=10, blank=True)
    verified = models.BooleanField(default=False)
    two_factor = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name or self.email


# =====================================================
# KYC
# =====================================================

class Kyc(models.Model):
    profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="kyc"
    )
    pan = models.CharField(max_length=20, blank=True)
    aadhaar = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    account_name = models.CharField(max_length=150, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    ifsc = models.CharField(max_length=20, blank=True)
    banks = models.JSONField(default=list, blank=True)
    aadhaar_mobile_linked = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"KYC - {self.profile}"


# =====================================================
# INVESTMENT
# =====================================================

class Investment(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Pending Bank Transfer", "Pending Bank Transfer"),
        ("Confirmed", "Confirmed"),
        ("Failed", "Failed"),
    ]

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="investments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    returns = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    order_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="Pending"
    )
    payment_method = models.CharField(max_length=50, blank=True)
    virtual_account = models.JSONField(default=dict, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.profile} - ₹{self.amount}"


# =====================================================
# WITHDRAWAL
# =====================================================

class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Rejected", "Rejected"),
    ]

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="withdrawals"
    )
    investment = models.ForeignKey(
        Investment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="withdrawals"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    requested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )
    processing_end = models.DateTimeField()
    bank_info = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    method = models.CharField(max_length=50, blank=True)
    utr = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.profile} - ₹{self.amount}"


# =====================================================
# SECURITY LOG
# =====================================================

class SecurityLog(models.Model):
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="security_logs"
    )
    action = models.CharField(max_length=150)
    detail = models.TextField(blank=True)
    at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.action


# =====================================================
# PERSONAL PANEL MODELS
# =====================================================

class FocusItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class CoreSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class LifeGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class CustomGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class Emi(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class Receivable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class Payable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class MoneyRule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class MindsetPoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class IncomeSource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class RoutineRow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    time = models.CharField(max_length=50)
    activity = models.CharField(max_length=255)
    duration = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.time} - {self.activity}"


class Skill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    hours = models.FloatField(default=0)
    target = models.PositiveIntegerField(default=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class GitaShloka(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sanskrit = models.TextField()
    eng = models.TextField(blank=True)
    hin = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sanskrit[:50]


class Journal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    happened = models.TextField(blank=True)
    feel = models.TextField(blank=True)
    learn = models.TextField(blank=True)
    want = models.TextField(blank=True)
    promise = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Journal - {self.date}"


class Note(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notes - {self.user.username}"


class Balance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sbi = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    punb = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    inv = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Balance - {self.user.username}"


class Setting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mission_end_date = models.DateField(null=True, blank=True)
    jaap_today = models.PositiveIntegerField(default=0)
    jaap_date = models.DateField(null=True, blank=True)
    monthly_need = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    finance_notes = models.TextField(blank=True)
    skills_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Settings - {self.user.username}"
