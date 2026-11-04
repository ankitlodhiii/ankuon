
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import base64
import hashlib
import hmac
import json
import secrets

from django.conf import settings
from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from app.models import (
    UserProfile,
    Investment,
    Withdrawal,
    Kyc,
    SecurityLog,
)

from .serializers import (
    UserProfileSerializer,
    InvestmentSerializer,
    WithdrawalSerializer,
)


# =====================================================
# OPTIONAL SERVICES
# =====================================================

try:
    from app.services.cashfree_va import create_virtual_account
except ImportError:
    create_virtual_account = None

try:
    from app.tasks import send_otp_email
except ImportError:
    send_otp_email = None


# =====================================================
# CONSTANTS
# =====================================================

ADMIN_EMAILS = [
    "admin@ankuon2.com",
    "ankitlodhiii06@gmail.com",
]

OTP_EXPIRY_SECONDS = 300
OTP_MAX_SENDS_PER_HOUR = 5
OTP_MAX_ATTEMPTS = 5

MIN_INVESTMENT = Decimal("10000")
MAX_INVESTMENT = Decimal("10000000")


# =====================================================
# COMMON HELPERS
# =====================================================

def get_profile(request):
    email = request.session.get("user_email")

    if not email:
        return None

    try:
        return UserProfile.objects.get(email=email)
    except UserProfile.DoesNotExist:
        return None


def get_admin_session(request):
    email = request.session.get("admin_email")

    return bool(
        email
        and email in ADMIN_EMAILS
        and request.session.get("is_admin") is True
    )


def parse_amount(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite():
            return None
        return amount
    except (InvalidOperation, TypeError, ValueError):
        return None


def log_security(profile, action, detail=""):
    SecurityLog.objects.create(
        profile=profile,
        action=action,
        detail=detail,
    )


# =====================================================
# USER OTP LOGIN
# =====================================================

class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        name = (request.data.get("name") or "").strip()

        if not email or not name:
            return Response(
                {"error": "Email and name required"},
                status=400,
            )

        if len(email) > 254 or "@" not in email:
            return Response({"error": "Invalid email"}, status=400)

        rate_key = f"otp_send_count:{email}"
        send_count = cache.get(rate_key, 0)

        if send_count >= OTP_MAX_SENDS_PER_HOUR:
            return Response(
                {"error": "Too many OTP requests. Try again later."},
                status=429,
            )

        profile, _ = UserProfile.objects.get_or_create(
            email=email,
            defaults={"name": name},
        )

        if name and profile.name != name:
            profile.name = name

        otp = str(secrets.randbelow(900000) + 100000)

        # Store OTP in cache with a five-minute expiry.
        cache.set(
            f"otp:{email}",
            otp,
            timeout=OTP_EXPIRY_SECONDS,
        )
        cache.set(
            f"otp_attempts:{email}",
            0,
            timeout=OTP_EXPIRY_SECONDS,
        )

        # Do not expose or print OTP.
        profile.otp = ""
        profile.save(update_fields=["name", "otp"])

        if send_otp_email is None:
            cache.delete(f"otp:{email}")
            return Response(
                {"error": "Email service is not configured"},
                status=503,
            )

        try:
            if hasattr(send_otp_email, "delay"):
                send_otp_email.delay(email, otp)
            else:
                send_otp_email(email, otp)

            cache.set(
                rate_key,
                send_count + 1,
                timeout=3600,
            )

        except Exception:
            cache.delete(f"otp:{email}")
            return Response(
                {"error": "Unable to send OTP. Please try again."},
                status=503,
            )

        return Response({"message": "OTP sent"}, status=200)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        otp = (request.data.get("otp") or "").strip()

        if not email or not otp:
            return Response(
                {"error": "Email and OTP required"},
                status=400,
            )

        stored_otp = cache.get(f"otp:{email}")
        attempts_key = f"otp_attempts:{email}"
        attempts = cache.get(attempts_key, 0)

        if not stored_otp:
            return Response(
                {"error": "OTP expired or not requested"},
                status=400,
            )

        if attempts >= OTP_MAX_ATTEMPTS:
            cache.delete(f"otp:{email}")
            return Response(
                {"error": "Too many incorrect attempts"},
                status=429,
            )

        if not secrets.compare_digest(str(stored_otp), otp):
            cache.set(
                attempts_key,
                attempts + 1,
                timeout=OTP_EXPIRY_SECONDS,
            )
            return Response({"error": "Invalid OTP"}, status=400)

        cache.delete(f"otp:{email}")
        cache.delete(attempts_key)

        try:
            profile = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        profile.verified = True
        profile.otp = ""
        profile.last_login = timezone.now()
        profile.save(
            update_fields=["verified", "otp", "last_login"]
        )

        request.session.cycle_key()
        request.session["user_email"] = email

        # A normal user login must never create an admin session.
        request.session.pop("admin_email", None)
        request.session.pop("is_admin", None)

        log_security(profile, "LOGIN")

        return Response(
            {
                "message": "Verified",
                "user": UserProfileSerializer(profile).data,
            },
            status=200,
        )


# =====================================================
# USER PROFILE
# =====================================================

class ProfileView(APIView):
    def get(self, request):
        profile = get_profile(request)

        if not profile:
            return Response({"error": "Unauthorized"}, status=401)

        return Response(
            UserProfileSerializer(profile).data,
            status=200,
        )


class UpdateProfileView(APIView):
    def post(self, request):
        profile = get_profile(request)

        if not profile:
            return Response({"error": "Unauthorized"}, status=401)

        name = (request.data.get("name") or "").strip()
        upi = (
            request.data.get("upi")
            or request.data.get("upi_id")
            or request.data.get("upiId")
            or ""
        ).strip()

        if name:
            profile.name = name

        if upi:
            profile.upi = upi

        profile.save()

        return Response(
            {
                "message": "Profile updated",
                "user": UserProfileSerializer(profile).data,
            },
            status=200,
        )


# =====================================================
# INVESTMENT
# =====================================================

class InvestView(APIView):
    def post(self, request):
        profile = get_profile(request)

        if not profile:
            return Response({"error": "Unauthorized"}, status=401)

        if profile.kyc_status != "Verified":
            return Response(
                {"error": "KYC verification required"},
                status=403,
            )

        amount = parse_amount(request.data.get("amount"))

        if amount is None:
            return Response({"error": "Invalid amount"}, status=400)

        if amount < MIN_INVESTMENT:
            return Response(
                {"error": "Minimum investment is ₹10,000"},
                status=400,
            )

        if amount > MAX_INVESTMENT:
            return Response(
                {"error": "Maximum investment is ₹1 Crore"},
                status=400,
            )

        payment_method = (
            request.data.get("payment_method")
            or request.data.get("paymentMethod")
            or "bank"
        )

        if payment_method not in ("bank", "upi"):
            return Response(
                {"error": "Unsupported payment method"},
                status=400,
            )

        order_id = (
            f"AO2-{timezone.now().strftime('%Y%m%d%H%M%S')}-"
            f"{secrets.token_hex(5).upper()}"
        )

        virtual_account = {}
        investment_status = "Pending"

        if payment_method == "bank":
            investment_status = "Pending Bank Transfer"

            request_va = request.data.get(
                "requestVirtualAccount",
                True,
            )

            if request_va or amount > Decimal("500000"):
                if create_virtual_account is None:
                    return Response(
                        {"error": "Bank transfer service unavailable"},
                        status=503,
                    )

                kyc = Kyc.objects.filter(profile=profile).first()

                try:
                    result = create_virtual_account(
                        order_id=order_id,
                        name=profile.name,
                        email=profile.email,
                        phone=(kyc.mobile if kyc else None) or profile.mobile,
                        pan=kyc.pan if kyc else None,
                        aadhaar=kyc.aadhaar if kyc else None,
                    )
                except Exception:
                    return Response(
                        {"error": "Unable to create bank transfer account"},
                        status=502,
                    )

                if result:
                    virtual_account = result

        investment = Investment.objects.create(
            profile=profile,
            amount=amount,
            order_id=order_id,
            status=investment_status,
            payment_method=payment_method,
            virtual_account=virtual_account,
        )

        return Response(
            {
                "orderId": investment.order_id,
                "order_id": investment.order_id,
                "status": investment.status,
                "virtualAccount": investment.virtual_account,
            },
            status=201,
        )


class CheckTransactionView(APIView):
    def get(self, request, order_id):
        profile = get_profile(request)

        if not profile:
            return Response({"error": "Unauthorized"}, status=401)

        investment = Investment.objects.filter(
            order_id=order_id,
            profile=profile,
        ).first()

        if not investment:
            return Response({"error": "Order not found"}, status=404)

        return Response(
            {
                "order_id": investment.order_id,
                "status": investment.status,
                "order_status": (
                    "PAID"
                    if investment.status == "Confirmed"
                    else investment.status
                ),
            },
            status=200,
        )


# =====================================================
# WITHDRAWAL
# =====================================================

class WithdrawView(APIView):
    def post(self, request):
        profile = get_profile(request)

        if not profile:
            return Response({"error": "Unauthorized"}, status=401)

        if profile.kyc_status != "Verified":
            return Response(
                {"error": "KYC verification required"},
                status=403,
            )

        kyc = Kyc.objects.filter(profile=profile).first()

        if not kyc or not kyc.bank_account or not kyc.ifsc:
            return Response(
                {"error": "Verified bank account required"},
                status=400,
            )

        investment_id = (
            request.data.get("investment_id")
            or request.data.get("investmentId")
        )

        amount = parse_amount(request.data.get("amount"))

        if amount is None or amount <= 0:
            return Response(
                {"error": "Enter a valid withdrawal amount"},
                status=400,
            )

        with transaction.atomic():
            investment = (
                Investment.objects.select_for_update()
                .filter(
                    id=investment_id,
                    profile=profile,
                    status="Confirmed",
                )
                .first()
            )

            if not investment:
                return Response(
                    {"error": "Confirmed investment not found"},
                    status=404,
                )

            already_withdrawn = (
                Withdrawal.objects.filter(
                    investment=investment,
                    status__in=["Pending", "Completed"],
                ).aggregate(total=models.Sum("amount"))["total"]
                or Decimal("0")
            )

            available = (
                investment.amount
                + investment.returns
                - already_withdrawn
            )

            if amount > available:
                return Response(
                    {"error": "Insufficient available balance"},
                    status=400,
                )

            withdrawal = Withdrawal.objects.create(
                profile=profile,
                investment=investment,
                amount=amount,
                processing_end=timezone.now() + timedelta(days=3),
                bank_info=(
                    f"Account name: {kyc.account_name or profile.name}; "
                    f"IFSC: {kyc.ifsc}"
                ),
                account_number=kyc.bank_account,
                method="NEFT/RTGS/IMPS",
            )

        return Response(
            {
                "message": "Withdrawal requested",
                "withdrawal": WithdrawalSerializer(withdrawal).data,
            },
            status=201,
        )


class CancelWithdrawalView(APIView):
    def post(self, request):
        profile = get_profile(request)

        if not profile:
            return Response({"error": "Unauthorized"}, status=401)

        withdrawal_id = (
            request.data.get("withdrawal_id")
            or request.data.get("withdrawalId")
        )

        with transaction.atomic():
            withdrawal = (
                Withdrawal.objects.select_for_update()
                .filter(
                    id=withdrawal_id,
                    profile=profile,
                )
                .first()
            )

            if not withdrawal:
                return Response({"error": "Not found"}, status=404)

            if withdrawal.status != "Pending":
                return Response(
                    {"error": "Only pending withdrawals can be cancelled"},
                    status=400,
                )

            if (
                timezone.now() - withdrawal.requested
            ).total_seconds() > 2 * 24 * 60 * 60:
                return Response(
                    {"error": "Cancellation period expired"},
                    status=400,
                )

            withdrawal.delete()

        return Response(
            {"message": "Withdrawal cancelled"},
            status=200,
        )


# =====================================================
# KYC SUBMISSION
# =====================================================

class KycVerificationView(APIView):
    def post(self, request):
        profile = get_profile(request)

        if not profile:
            return Response({"error": "Unauthorized"}, status=401)

        pan = (request.data.get("pan") or "").strip().upper()
        aadhaar = (
            request.data.get("aadhaar") or ""
        ).replace(" ", "").replace("-", "")
        mobile = (
            request.data.get("mobile") or ""
        ).replace(" ", "")

        account_name = (
            request.data.get("accountName")
            or request.data.get("account_name")
            or ""
        ).strip()

        bank_account = (
            request.data.get("bankAccount")
            or request.data.get("bank_account")
            or ""
        ).replace(" ", "")

        ifsc = (request.data.get("ifsc") or "").strip().upper()

        if pan and not (
            len(pan) == 10
            and pan[:5].isalpha()
            and pan[5:9].isdigit()
            and pan[9].isalpha()
        ):
            return Response({"error": "Invalid PAN"}, status=400)

        if aadhaar and not (
            aadhaar.isdigit() and len(aadhaar) == 12
        ):
            return Response({"error": "Invalid Aadhaar"}, status=400)

        if mobile and not (
            mobile.isdigit()
            and len(mobile) == 10
            and mobile[0] in "6789"
        ):
            return Response({"error": "Invalid mobile"}, status=400)

        if bank_account and not (
            bank_account.isdigit()
            and 9 <= len(bank_account) <= 18
        ):
            return Response(
                {"error": "Invalid bank account"},
                status=400,
            )

        if ifsc and not (
            len(ifsc) == 11
            and ifsc[:4].isalpha()
            and ifsc[4] == "0"
            and ifsc[5:].isalnum()
        ):
            return Response({"error": "Invalid IFSC"}, status=400)

        kyc, _ = Kyc.objects.get_or_create(profile=profile)

        if pan:
            kyc.pan = pan

        if aadhaar:
            kyc.aadhaar = aadhaar

        if mobile:
            kyc.mobile = mobile
            profile.mobile = mobile
            profile.save(update_fields=["mobile"])

        if account_name:
            kyc.account_name = account_name

        if bank_account:
            kyc.bank_account = bank_account

        if ifsc:
            kyc.ifsc = ifsc

        # Submission does NOT automatically verify KYC.
        # Verification must come from a trusted verification process.
        kyc.save()

        log_security(profile, "KYC_SUBMITTED")

        return Response(
            {
                "message": "KYC details submitted for verification",
                "kycStatus": profile.kyc_status,
            },
            status=200,
        )


# =====================================================
# CASHFREE WEBHOOK
# =====================================================

class CashfreeWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def _verify_signature(self, raw_body, signature, timestamp):
        secret = getattr(settings, "CASHFREE_SECRET_KEY", "")

        if not secret or not signature or not timestamp:
            return False

        try:
            body = raw_body.decode("utf-8")

            signed_payload = f"{timestamp}{body}"

            computed = base64.b64encode(
                hmac.new(
                    secret.encode("utf-8"),
                    signed_payload.encode("utf-8"),
                    hashlib.sha256,
                ).digest()
            ).decode("utf-8")

            return hmac.compare_digest(computed, signature)

        except Exception:
            return False

    def post(self, request):
        raw_body = request.body

        signature = request.headers.get("x-webhook-signature")
        timestamp = request.headers.get("x-webhook-timestamp")

        if not self._verify_signature(
            raw_body,
            signature,
            timestamp,
        ):
            return Response(
                {"error": "Invalid webhook signature"},
                status=401,
            )

        try:
            data = json.loads(raw_body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return Response({"error": "Invalid JSON"}, status=400)

        event_type = data.get("type") or data.get("event") or ""

        if event_type not in (
            "PAYMENT_SUCCESS_WEBHOOK",
            "PAYMENT_SUCCESS",
        ):
            return Response({"status": "ignored"}, status=200)

        payload = data.get("data") or {}
        order = payload.get("order") or {}
        payment = payload.get("payment") or {}

        order_id = (
            order.get("order_id")
            or payment.get("order_id")
        )

        payment_amount = (
            payment.get("payment_amount")
            or order.get("order_amount")
        )

        utr = (
            payment.get("bank_reference")
            or payment.get("cf_payment_id")
            or ""
        )

        if not order_id or payment_amount is None:
            return Response(
                {"error": "Missing order or payment amount"},
                status=400,
            )

        amount = parse_amount(payment_amount)

        if amount is None:
            return Response(
                {"error": "Invalid payment amount"},
                status=400,
            )

        updated = self._confirm_investment(
            order_id=order_id,
            amount=amount,
            utr=utr,
        )

        return Response(
            {
                "status": "ok",
                "order_id": order_id,
                "updated": updated,
            },
            status=200,
        )

    def _confirm_investment(self, order_id, amount, utr):
        with transaction.atomic():
            investment = (
                Investment.objects.select_for_update()
                .filter(order_id=order_id)
                .first()
            )

            if not investment:
                return False

            if investment.status == "Confirmed":
                return True

            if investment.status not in (
                "Pending",
                "Pending Bank Transfer",
            ):
                return False

            if investment.amount != amount:
                return False

            investment.status = "Confirmed"
            investment.confirmed_at = timezone.now()
            investment.save(
                update_fields=["status", "confirmed_at"]
            )

            log_security(
                investment.profile,
                "PAYMENT_CONFIRMED",
                f"order={order_id}; utr={utr}",
            )

        return True


# =====================================================
# ADMIN LOGIN
# =====================================================

class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password") or ""

        admin_password = getattr(settings, "ADMIN_PASSWORD", "")

        if not admin_password:
            return Response(
                {"error": "Admin password is not configured"},
                status=503,
            )

        if (
            email not in ADMIN_EMAILS
            or not hmac.compare_digest(
                str(password),
                str(admin_password),
            )
        ):
            return Response(
                {"error": "Invalid admin credentials"},
                status=401,
            )

        request.session.cycle_key()
        request.session["admin_email"] = email
        request.session["is_admin"] = True

        return Response(
            {
                "message": "Admin login successful",
                "admin": {"email": email},
            },
            status=200,
        )


# =====================================================
# ADMIN STATISTICS
# =====================================================

class AdminStatsView(APIView):
    def get(self, request):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        total_users = UserProfile.objects.count()

        total_invested = (
            Investment.objects.filter(status="Confirmed")
            .aggregate(total=models.Sum("amount"))["total"]
            or Decimal("0")
        )

        pending_bank = Investment.objects.filter(
            status="Pending Bank Transfer"
        ).count()

        pending_withdrawals = Withdrawal.objects.filter(
            status="Pending"
        ).count()

        return Response(
            {
                "totalUsers": total_users,
                "totalInvested": str(total_invested),
                "pendingBankTransfers": pending_bank,
                "pendingWithdrawals": pending_withdrawals,
            },
            status=200,
        )


# =====================================================
# ADMIN USER MANAGEMENT
# =====================================================

class AdminSearchUsersView(APIView):
    def get(self, request):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        query = (request.GET.get("q") or "").strip()

        queryset = UserProfile.objects.all()

        if query:
            queryset = queryset.filter(
                models.Q(email__icontains=query)
                | models.Q(name__icontains=query)
                | models.Q(mobile__icontains=query)
            )

        result = []

        for profile in queryset[:50]:
            total = (
                profile.investments.filter(status="Confirmed")
                .aggregate(total=models.Sum("amount"))["total"]
                or Decimal("0")
            )

            result.append(
                {
                    "id": profile.id,
                    "email": profile.email,
                    "name": profile.name,
                    "kycStatus": profile.kyc_status,
                    "totalInvested": str(total),
                }
            )

        return Response(result, status=200)


class AdminUserDetailView(APIView):
    def get(self, request, user_id):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        profile = UserProfile.objects.filter(id=user_id).first()

        if not profile:
            return Response({"error": "User not found"}, status=404)

        return Response(
            UserProfileSerializer(profile).data,
            status=200,
        )


class AdminUserInvestmentsView(APIView):
    def get(self, request, user_id):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        investments = Investment.objects.filter(
            profile_id=user_id
        ).order_by("-date")

        return Response(
            InvestmentSerializer(investments, many=True).data,
            status=200,
        )


class AdminUserWithdrawalsView(APIView):
    def get(self, request, user_id):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        withdrawals = Withdrawal.objects.filter(
            profile_id=user_id
        ).order_by("-requested")

        return Response(
            WithdrawalSerializer(withdrawals, many=True).data,
            status=200,
        )


# =====================================================
# ADMIN WITHDRAWAL MANAGEMENT
# =====================================================

class AdminPendingWithdrawalsView(APIView):
    def get(self, request):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        withdrawals = (
            Withdrawal.objects.filter(status="Pending")
            .select_related("profile")
            .order_by("requested")
        )

        result = []

        for withdrawal in withdrawals:
            item = dict(WithdrawalSerializer(withdrawal).data)
            item["userEmail"] = withdrawal.profile.email
            item["userName"] = withdrawal.profile.name
            result.append(item)

        return Response(result, status=200)


class AdminProcessWithdrawalView(APIView):
    def post(self, request, withdrawal_id):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        utr = (request.data.get("utr") or "").strip()
        notes = request.data.get("notes", "")

        if not utr:
            return Response({"error": "UTR required"}, status=400)

        with transaction.atomic():
            withdrawal = (
                Withdrawal.objects.select_for_update()
                .filter(
                    id=withdrawal_id,
                    status="Pending",
                )
                .first()
            )

            if not withdrawal:
                return Response({"error": "Not found"}, status=404)

            withdrawal.status = "Completed"
            withdrawal.utr = utr
            withdrawal.notes = notes
            withdrawal.save(
                update_fields=["status", "utr", "notes"]
            )

            log_security(
                withdrawal.profile,
                "WITHDRAWAL_COMPLETED",
                f"withdrawal={withdrawal.id}; utr={utr}",
            )

        return Response(
            {"message": "Withdrawal processed"},
            status=200,
        )


class AdminRejectWithdrawalView(APIView):
    def post(self, request, withdrawal_id):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        reason = (
            request.data.get("reason")
            or "Rejected by admin"
        )

        with transaction.atomic():
            withdrawal = (
                Withdrawal.objects.select_for_update()
                .filter(
                    id=withdrawal_id,
                    status="Pending",
                )
                .first()
            )

            if not withdrawal:
                return Response({"error": "Not found"}, status=404)

            withdrawal.status = "Rejected"
            withdrawal.notes = reason
            withdrawal.save(
                update_fields=["status", "notes"]
            )

            log_security(
                withdrawal.profile,
                "WITHDRAWAL_REJECTED",
                f"withdrawal={withdrawal.id}",
            )

        return Response({"message": "Rejected"}, status=200)


# =====================================================
# ADMIN BANK TRANSFER MANAGEMENT
# =====================================================

class AdminPendingBankTransfersView(APIView):
    def get(self, request):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        investments = (
            Investment.objects.filter(
                status="Pending Bank Transfer"
            )
            .select_related("profile")
            .order_by("date")
        )

        result = []

        for investment in investments:
            item = dict(InvestmentSerializer(investment).data)
            item["userEmail"] = investment.profile.email
            item["userName"] = investment.profile.name
            result.append(item)

        return Response(result, status=200)


class AdminConfirmBankTransferView(APIView):
    def post(self, request, investment_id):
        if not get_admin_session(request):
            return Response({"error": "Unauthorized"}, status=401)

        utr = (request.data.get("utr") or "").strip()

        if not utr:
            return Response({"error": "UTR required"}, status=400)

        with transaction.atomic():
            investment = (
                Investment.objects.select_for_update()
                .filter(
                    id=investment_id,
                    status="Pending Bank Transfer",
                )
                .first()
            )

            if not investment:
                return Response({"error": "Not found"}, status=404)

            investment.status = "Confirmed"
            investment.confirmed_at = timezone.now()
            investment.save(
                update_fields=["status", "confirmed_at"]
            )

            log_security(
                investment.profile,
                "BANK_TRANSFER_CONFIRMED",
                f"order={investment.order_id}; utr={utr}",
            )

        return Response(
            {"message": "Bank transfer confirmed"},
            status=200,
        )
