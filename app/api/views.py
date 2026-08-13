# app/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import timedelta
import random
import json

from .serializers import UserProfileSerializer, InvestmentSerializer, WithdrawalSerializer
from app.models import UserProfile, Investment, Withdrawal, Kyc, SecurityLog

try:
    from app.services.cashfree_va import create_virtual_account
except ImportError:
    def create_virtual_account(*args, **kwargs):
        return None

try:
    from app.services.cashfree_webhook import verify_cashfree_signature
except ImportError:
    def verify_cashfree_signature(*args, **kwargs):
        return True

try:
    from app.tasks import send_otp_email
except ImportError:
    def send_otp_email(email, otp):
        print(f'[OTP] {email}: {otp}')


def get_profile(request):
    email = request.session.get('user_email')
    if not email:
        return None
    try:
        return UserProfile.objects.select_related('kyc').get(email=email)
    except UserProfile.DoesNotExist:
        return None


# ==================== USER APIs ====================

class SendOTPView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        name = request.data.get('name', '').strip()
        if not email or not name:
            return Response({'error': 'Email and name required'}, status=400)

        profile, _ = UserProfile.objects.get_or_create(
            email=email, defaults={'name': name}
        )
        if name and profile.name != name:
            profile.name = name

        otp = str(random.randint(100000, 999999))
        profile.otp = otp
        profile.save()

        print(f'[DEMO OTP] {email}: {otp}')

        try:
            send_otp_email.delay(email, otp)
        except Exception:
            print(f'[DEMO OTP fallback] {email}: {otp}')

        return Response({'message': 'OTP sent'}, status=200)


class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        otp = request.data.get('otp', '').strip()
        try:
            profile = UserProfile.objects.select_related('kyc').get(email=email)
            if profile.otp != otp:
                return Response({'error': 'Invalid OTP'}, status=400)

            profile.verified = True
            profile.otp = None
            profile.last_login = timezone.now()
            profile.save()

            request.session['user_email'] = email
            SecurityLog.objects.create(user=profile, action='LOGIN')

            return Response({
                'message': 'Verified',
                'user': UserProfileSerializer(profile).data
            }, status=200)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class ProfileView(APIView):
    def get(self, request):
        profile = get_profile(request)
        if not profile:
            return Response({'error': 'Unauthorized'}, status=401)
        return Response(UserProfileSerializer(profile).data, status=200)


class InvestView(APIView):
    def post(self, request):
        profile = get_profile(request)
        if not profile:
            return Response({'error': 'Unauthorized'}, status=401)

        if profile.kyc_status != 'Verified':
            return Response({'error': 'KYC verification required'}, status=403)

        amount = request.data.get('amount')
        payment_method = (
            request.data.get('payment_method')
            or request.data.get('paymentMethod')
            or 'bank'
        )
        request_va = request.data.get('requestVirtualAccount', True)

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return Response({'error': 'Invalid amount'}, status=400)

        if amount < 10000:
            return Response({'error': 'Minimum amount is ₹10,000'}, status=400)
        if amount > 10000000:
            return Response({'error': 'Maximum amount is ₹1 Crore'}, status=400)

        order_id = f"AO2-{timezone.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"

        virtual_account = None
        status_value = 'Pending'

        if payment_method == 'bank':
            status_value = 'Pending Bank Transfer'
            if request_va or amount > 500000:
                kyc = getattr(profile, 'kyc', None)
                virtual_account = create_virtual_account(
                    order_id=order_id,
                    name=profile.name,
                    email=profile.email,
                    phone=getattr(kyc, 'mobile', None) or profile.mobile,
                    pan=getattr(kyc, 'pan', None),
                    aadhaar=getattr(kyc, 'aadhaar', None),
                )

        Investment.objects.create(
            user=profile,
            amount=amount,
            order_id=order_id,
            status=status_value,
            payment_method=payment_method,
            virtual_account=virtual_account,
        )

        response_data = {
            'orderId': order_id,
            'order_id': order_id,
            'status': status_value,
        }
        if virtual_account:
            response_data['virtualAccount'] = virtual_account

        return Response(response_data, status=200)


class CheckTransactionView(APIView):
    def get(self, request, order_id):
        profile = get_profile(request)
        if not profile:
            return Response({'error': 'Unauthorized'}, status=401)
        try:
            inv = Investment.objects.get(order_id=order_id, user=profile)
            return Response({
                'order_id': inv.order_id,
                'status': inv.status,
                'order_status': 'PAID' if inv.status == 'Confirmed' else inv.status,
            }, status=200)
        except Investment.DoesNotExist:
            return Response({'error': 'Order not found'}, status=404)


class WithdrawView(APIView):
    def post(self, request):
        profile = get_profile(request)
        if not profile:
            return Response({'error': 'Unauthorized'}, status=401)
        if profile.kyc_status != 'Verified':
            return Response({'error': 'KYC verification required'}, status=403)

        kyc = getattr(profile, 'kyc', None)
        if not kyc or not kyc.bank_account or not kyc.ifsc:
            return Response({'error': 'Verified bank account required for withdrawals'}, status=400)

        investment_id = request.data.get('investment_id') or request.data.get('investmentId')
        amount = request.data.get('amount')

        try:
            investment = Investment.objects.get(id=investment_id, user=profile)
        except Investment.DoesNotExist:
            return Response({'error': 'Investment not found'}, status=404)

        if investment.status != 'Confirmed':
            return Response({'error': 'Only confirmed investments can be withdrawn'}, status=400)

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = float(investment.amount + investment.returns)

        max_amount = float(investment.amount + investment.returns)
        if amount > max_amount:
            return Response({'error': 'Insufficient balance'}, status=400)

        withdrawal = Withdrawal.objects.create(
            user=profile,
            investment=investment,
            amount=amount,
            processing_end=timezone.now() + timedelta(days=3),
            bank_account=kyc.bank_account,
            ifsc=kyc.ifsc,
            account_name=kyc.account_name or profile.name,
            method='NEFT/RTGS/IMPS',
        )
        return Response({
            'message': 'Withdrawal requested to your verified bank account',
            'withdrawal': WithdrawalSerializer(withdrawal).data
        }, status=200)


class CancelWithdrawalView(APIView):
    def post(self, request):
        profile = get_profile(request)
        if not profile:
            return Response({'error': 'Unauthorized'}, status=401)

        withdrawal_id = request.data.get('withdrawal_id') or request.data.get('withdrawalId')
        try:
            wd = Withdrawal.objects.get(id=withdrawal_id, user=profile)
            if (timezone.now() - wd.requested).total_seconds() > 2 * 24 * 60 * 60:
                return Response({'error': 'Cannot cancel: past cancellation window'}, status=400)
            if wd.status != 'Pending':
                return Response({'error': 'Only pending withdrawals can be cancelled'}, status=400)
            wd.delete()
            return Response({'message': 'Withdrawal cancelled'}, status=200)
        except Withdrawal.DoesNotExist:
            return Response({'error': 'Withdrawal not found'}, status=404)


class UpdateProfileView(APIView):
    def post(self, request):
        profile = get_profile(request)
        if not profile:
            return Response({'error': 'Unauthorized'}, status=401)

        name = request.data.get('name')
        upi_id = request.data.get('upi_id') or request.data.get('upiId', '')

        if name:
            profile.name = name.strip()
        if upi_id:
            profile.upi_id = upi_id.strip()
        profile.save()

        return Response({
            'message': 'Profile updated',
            'user': UserProfileSerializer(profile).data
        }, status=200)


class KycVerificationView(APIView):
    def post(self, request):
        profile = get_profile(request)
        if not profile:
            return Response({'error': 'Unauthorized'}, status=401)

        pan = (request.data.get('pan') or '').strip().upper()
        aadhaar = (request.data.get('aadhaar') or '').replace(' ', '')
        mobile = (request.data.get('mobile') or '').replace(' ', '')
        account_name = (request.data.get('accountName') or request.data.get('account_name') or '').strip()
        bank_account = (request.data.get('bankAccount') or request.data.get('bank_account') or '').replace(' ', '')
        ifsc = (request.data.get('ifsc') or '').strip().upper()

        kyc, _ = Kyc.objects.get_or_create(user=profile)

        if pan:
            if not (len(pan) == 10 and pan[:5].isalpha() and pan[5:9].isdigit() and pan[9].isalpha()):
                return Response({'error': 'Invalid PAN'}, status=400)
            kyc.pan = pan
        if aadhaar:
            if not (aadhaar.isdigit() and len(aadhaar) == 12):
                return Response({'error': 'Invalid Aadhaar'}, status=400)
            kyc.aadhaar = aadhaar
        if mobile:
            if not (mobile.isdigit() and len(mobile) == 10 and mobile[0] in '6789'):
                return Response({'error': 'Invalid mobile'}, status=400)
            kyc.mobile = mobile
            profile.mobile = mobile
            profile.save()

        if request.data.get('aadhaarMobileLinked') or request.data.get('otp_verified'):
            kyc.aadhaar_mobile_linked = True

        if account_name:
            kyc.account_name = account_name
        if bank_account:
            if not (bank_account.isdigit() and 9 <= len(bank_account) <= 18):
                return Response({'error': 'Invalid bank account number'}, status=400)
            kyc.bank_account = bank_account
        if ifsc:
            if not (len(ifsc) == 11 and ifsc[:4].isalpha() and ifsc[4] == '0'):
                return Response({'error': 'Invalid IFSC'}, status=400)
            kyc.ifsc = ifsc

        if kyc.pan and kyc.aadhaar and kyc.mobile and kyc.bank_account and kyc.ifsc:
            kyc.aadhaar_mobile_linked = True
            kyc.verified_at = timezone.now()
            profile.kyc_status = 'Verified'
            profile.save()
            kyc.banks = [{
                'id': 1,
                'bankAccount': kyc.bank_account,
                'ifsc': kyc.ifsc,
                'accountName': kyc.account_name,
                'isPrimary': True,
            }]
            SecurityLog.objects.create(
                user=profile,
                action='KYC_VERIFIED',
                detail='Aadhaar + Bank',
            )

        kyc.save()

        return Response({
            'message': 'KYC updated',
            'user': UserProfileSerializer(profile).data,
            'kycStatus': profile.kyc_status,
        }, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class CashfreeWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            raw_body = request.body.decode('utf-8')
        except Exception:
            raw_body = ''

        timestamp = (
            request.headers.get('x-webhook-timestamp')
            or request.META.get('HTTP_X_WEBHOOK_TIMESTAMP', '')
        )
        signature = (
            request.headers.get('x-webhook-signature')
            or request.META.get('HTTP_X_WEBHOOK_SIGNATURE', '')
        )

        if not verify_cashfree_signature(raw_body, timestamp, signature):
            print('[Cashfree Webhook] Invalid signature')
            return Response({'error': 'Invalid signature'}, status=401)

        try:
            data = json.loads(raw_body) if raw_body else (request.data or {})
        except json.JSONDecodeError:
            data = request.data or {}

        event_type = data.get('type') or data.get('event') or ''
        print(f'[Cashfree Webhook] type={event_type}')

        order_id = None
        utr = None
        payment_status = None

        if event_type in (
            'PAYMENT_SUCCESS_WEBHOOK',
            'PAYMENT_FAILED_WEBHOOK',
            'PAYMENT_USER_DROPPED_WEBHOOK',
        ):
            order = (data.get('data') or {}).get('order') or {}
            payment = (data.get('data') or {}).get('payment') or {}

            order_id = order.get('order_id')
            payment_status = payment.get('payment_status')
            utr = payment.get('bank_reference')

            method = payment.get('payment_method') or {}
            vba = method.get('vba_transfer') or {}
            if vba:
                order_id = order_id or vba.get('vaccount_id')
                utr = utr or vba.get('utr')

        elif event_type == 'AMOUNT_COLLECTED' or data.get('event') == 'AMOUNT_COLLECTED':
            order_id = data.get('vAccountId') or data.get('vaccount_id')
            utr = data.get('utr')
            payment_status = 'SUCCESS'

        if order_id and payment_status == 'SUCCESS':
            updated = Investment.objects.filter(
                order_id=order_id,
                status__in=['Pending', 'Pending Bank Transfer'],
            ).update(
                status='Confirmed',
                confirmed_at=timezone.now(),
            )
            print(f'[Cashfree Webhook] order={order_id} confirmed={updated} utr={utr}')

            if updated:
                inv = Investment.objects.filter(order_id=order_id).select_related('user').first()
                if inv:
                    SecurityLog.objects.create(
                        user=inv.user,
                        action='PAYMENT_CONFIRMED',
                        detail=f'Order {order_id} UTR={utr or "-"}',
                    )

        elif order_id and payment_status in ('FAILED', 'USER_DROPPED', 'CANCELLED'):
            Investment.objects.filter(
                order_id=order_id,
                status__in=['Pending', 'Pending Bank Transfer'],
            ).update(status='Failed')
            print(f'[Cashfree Webhook] order={order_id} marked Failed')

        return Response({'status': 'ok'}, status=200)


# ==================== ADMIN ====================

ADMIN_EMAILS = [
    'admin@ankuon2.com',
    'ankitlodhiii06@gmail.com',
]


def is_admin(request):
    email = request.session.get('admin_email') or request.session.get('user_email')
    return email in ADMIN_EMAILS


class AdminLoginView(APIView):
    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if email in ADMIN_EMAILS and password == getattr(settings, 'ADMIN_PASSWORD', 'AnkuOn2Admin@2026'):
            request.session['admin_email'] = email
            request.session['user_email'] = email
            return Response({
                'token': 'admin-session',
                'admin': {'email': email}
            }, status=200)
        return Response({'error': 'Invalid admin credentials'}, status=401)


class AdminStatsView(APIView):
    def get(self, request):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)

        total_users = UserProfile.objects.count()
        total_invested = Investment.objects.filter(status='Confirmed').aggregate(
            s=models.Sum('amount')
        )['s'] or 0
        pending_bank = Investment.objects.filter(status='Pending Bank Transfer').count()
        pending_wd = Withdrawal.objects.filter(status='Pending').count()

        return Response({
            'totalUsers': total_users,
            'totalInvested': float(total_invested),
            'pendingBankTransfers': pending_bank,
            'pendingWithdrawals': pending_wd,
        }, status=200)


class AdminSearchUsersView(APIView):
    def get(self, request):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)

        q = request.GET.get('q', '').strip()
        qs = UserProfile.objects.all()
        if q:
            qs = qs.filter(
                models.Q(email__icontains=q) |
                models.Q(name__icontains=q) |
                models.Q(mobile__icontains=q)
            )

        result = []
        for u in qs[:50]:
            total = u.investments.filter(status='Confirmed').aggregate(
                s=models.Sum('amount')
            )['s'] or 0
            result.append({
                'id': u.id,
                'email': u.email,
                'name': u.name,
                'kycStatus': u.kyc_status,
                'totalInvested': float(total),
            })
        return Response(result, status=200)


class AdminUserDetailView(APIView):
    def get(self, request, user_id):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)
        try:
            profile = UserProfile.objects.select_related('kyc').get(id=user_id)
            return Response(UserProfileSerializer(profile).data, status=200)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class AdminUserInvestmentsView(APIView):
    def get(self, request, user_id):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)
        invs = Investment.objects.filter(user_id=user_id).order_by('-date')
        return Response(InvestmentSerializer(invs, many=True).data, status=200)


class AdminUserWithdrawalsView(APIView):
    def get(self, request, user_id):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)
        wds = Withdrawal.objects.filter(user_id=user_id).order_by('-requested')
        return Response(WithdrawalSerializer(wds, many=True).data, status=200)


class AdminPendingWithdrawalsView(APIView):
    def get(self, request):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)
        wds = Withdrawal.objects.filter(status='Pending').select_related('user').order_by('requested')
        data = []
        for w in wds:
            item = WithdrawalSerializer(w).data
            item['userEmail'] = w.user.email
            item['userName'] = w.user.name
            data.append(item)
        return Response(data, status=200)


class AdminProcessWithdrawalView(APIView):
    def post(self, request, withdrawal_id):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)
        utr = request.data.get('utr', '').strip()
        notes = request.data.get('notes', '')
        if not utr:
            return Response({'error': 'UTR required'}, status=400)
        try:
            wd = Withdrawal.objects.get(id=withdrawal_id, status='Pending')
            wd.status = 'Completed'
            wd.utr = utr
            wd.notes = notes
            wd.save()
            return Response({'message': 'Withdrawal processed'}, status=200)
        except Withdrawal.DoesNotExist:
            return Response({'error': 'Withdrawal not found'}, status=404)


class AdminRejectWithdrawalView(APIView):
    def post(self, request, withdrawal_id):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)
        reason = request.data.get('reason', 'Rejected by admin')
        try:
            wd = Withdrawal.objects.get(id=withdrawal_id, status='Pending')
            wd.status = 'Rejected'
            wd.notes = reason
            wd.save()
            return Response({'message': 'Withdrawal rejected'}, status=200)
        except Withdrawal.DoesNotExist:
            return Response({'error': 'Withdrawal not found'}, status=404)


class AdminPendingBankTransfersView(APIView):
    def get(self, request):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)
        invs = Investment.objects.filter(
            status='Pending Bank Transfer'
        ).select_related('user').order_by('date')
        data = []
        for inv in invs:
            item = InvestmentSerializer(inv).data
            item['userEmail'] = inv.user.email
            item['userName'] = inv.user.name
            data.append(item)
        return Response(data, status=200)


class AdminConfirmBankTransferView(APIView):
    def post(self, request, investment_id):
        if not is_admin(request):
            return Response({'error': 'Unauthorized'}, status=401)
        utr = request.data.get('utr', '').strip()
        if not utr:
            return Response({'error': 'UTR required'}, status=400)
        try:
            inv = Investment.objects.get(id=investment_id, status='Pending Bank Transfer')
            inv.status = 'Confirmed'
            inv.confirmed_at = timezone.now()
            inv.save()
            return Response({'message': 'Bank transfer confirmed'}, status=200)
        except Investment.DoesNotExist:
            return Response({'error': 'Investment not found'}, status=404)
