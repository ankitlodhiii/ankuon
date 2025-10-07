# app/api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .serializers import UserProfileSerializer, InvestmentSerializer, WithdrawalSerializer
from ..models import UserProfile, Investment, Withdrawal
import random
from datetime import timedelta
from django.utils import timezone
from app.tasks import send_otp_email

try:
 from cashfree_pg_sdk.payments import PaymentGateway
except ImportError:
    # Mock PaymentGateway for testing
    class PaymentGateway:
        def __init__(self, mode):
            self.mode = mode
        def set_app_id(self, app_id):
            self.app_id = app_id
        def set_secret_key(self, secret_key):
            self.secret_key = secret_key
        def create_order(self, order_data):
            return {'status': 'OK', 'order_id': f'MOCK_ORDER_{random.randint(1000, 9999)}', 'payment_link': 'https://mock.payment.link'}
        def verify_order_status(self, order_id):
            return {'order_status': 'PAID'}
        def upi_collect(self, data):
            return {'order_id': data['order_id']}

class SendOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        name = request.data.get('name')
        if not email or not name:
            return Response({'error': 'Email and name required'}, status=status.HTTP_400_BAD_REQUEST)
        profile, created = UserProfile.objects.get_or_create(email=email, defaults={'name': name})
        otp = str(random.randint(100000, 999999))
        profile.otp = otp
        profile.save()
        send_otp_email.delay(email, otp)
        return Response({'message': 'OTP sent'}, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        try:
            profile = UserProfile.objects.get(email=email)
            if profile.otp == otp:
                profile.verified = True
                profile.otp = None
                profile.save()
                request.session['user_email'] = email
                return Response({'message': 'Verified', 'user': UserProfileSerializer(profile).data}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class InvestView(APIView):
    def post(self, request):
        if not request.session.get('user_email'):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method')
        user_email = request.session['user_email']
        try:
            profile = UserProfile.objects.get(email=user_email)
            if profile.kyc_status != 'Verified':
                return Response({'error': 'KYC verification required'}, status=status.HTTP_403_FORBIDDEN)
            cashfree = PaymentGateway(mode='PRODUCTION' if not settings.DEBUG else 'SANDBOX')
            cashfree.set_app_id(settings.CASHFREE_APP_ID)
            cashfree.set_secret_key(settings.CASHFREE_SECRET_KEY)
            order_data = {
                'order_amount': float(amount),
                'order_currency': 'INR',
                'customer_email': profile.email,
                'customer_name': profile.name,
                'order_note': f'Investment_{timezone.now()}',
            }
            response = cashfree.create_order(order_data)
            if response.get('status') == 'OK':
                investment = Investment(user=profile, amount=amount, order_id=response['order_id'], status='Pending')
                investment.save()
                if payment_method == 'qr':
                    return Response({'qr_data': response['payment_link'], 'order_id': response['order_id']}, status=status.HTTP_200_OK)
                elif payment_method == 'collect':
                    collect_response = cashfree.upi_collect({
                        'order_id': response['order_id'],
                        'vpa': profile.upi_id,
                        'order_amount': float(amount),
                        'customer_email': profile.email,
                        'customer_name': profile.name,
                    })
                    return Response({'order_id': collect_response.get('order_id', response['order_id'])}, status=status.HTTP_200_OK)
            return Response({'error': 'Payment creation failed'}, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CheckTransactionView(APIView):
    def get(self, request, order_id):
        if not request.session.get('user_email'):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            cashfree = PaymentGateway(mode='PRODUCTION' if not settings.DEBUG else 'SANDBOX')
            cashfree.set_app_id(settings.CASHFREE_APP_ID)
            cashfree.set_secret_key(settings.CASHFREE_SECRET_KEY)
            response = cashfree.verify_order_status(order_id)
            if response.get('order_status') == 'PAID':
                try:
                    investment = Investment.objects.get(order_id=order_id)
                    investment.status = 'Confirmed'
                    investment.save()
                except Investment.DoesNotExist:
                    pass
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class WithdrawView(APIView):
    def post(self, request):
        if not request.session.get('user_email'):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        user_email = request.session['user_email']
        try:
            profile = UserProfile.objects.get(email=user_email)
            if profile.kyc_status != 'Verified':
                return Response({'error': 'KYC verification required'}, status=status.HTTP_403_FORBIDDEN)
            investment_id = request.data.get('investment_id')
            amount = request.data.get('amount')
            try:
                investment = Investment.objects.get(id=investment_id, user=profile)
                if not profile.upi_id:
                    return Response({'error': 'UPI ID required'}, status=status.HTTP_400_BAD_REQUEST)
                if float(amount) > float(investment.amount + investment.returns):
                    return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
                withdrawal = Withdrawal(
                    user=profile,
                    investment=investment,
                    amount=amount,
                    processing_end=timezone.now() + timedelta(days=3),
                    upi_id=profile.upi_id
                )
                withdrawal.save()
                return Response({'message': 'Withdrawal requested'}, status=status.HTTP_200_OK)
            except Investment.DoesNotExist:
                return Response({'error': 'Investment not found'}, status=status.HTTP_404_NOT_FOUND)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class CancelWithdrawalView(APIView):
    def post(self, request):
        if not request.session.get('user_email'):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        withdrawal_id = request.data.get('withdrawal_id')
        try:
            withdrawal = Withdrawal.objects.get(id=withdrawal_id, user__email=request.session['user_email'])
            if (timezone.now() - withdrawal.requested).total_seconds() > 2 * 24 * 60 * 60:
                return Response({'error': 'Cannot cancel: Processing started'}, status=status.HTTP_400_BAD_REQUEST)
            withdrawal.delete()
            return Response({'message': 'Withdrawal cancelled'}, status=status.HTTP_200_OK)
        except Withdrawal.DoesNotExist:
            return Response({'error': 'Withdrawal not found'}, status=status.HTTP_404_NOT_FOUND)

class UpdateProfileView(APIView):
    def post(self, request):
        if not request.session.get('user_email'):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        name = request.data.get('name')
        upi_id = request.data.get('upi_id', '')
        try:
            profile = UserProfile.objects.get(email=request.session['user_email'])
            profile.name = name
            if upi_id:
                profile.upi_id = upi_id
            profile.save()
            return Response({'message': 'Profile updated', 'user': UserProfileSerializer(profile).data}, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class KycVerificationView(APIView):
    def post(self, request):
        if not request.session.get('user_email'):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            profile = UserProfile.objects.get(email=request.session['user_email'])
            profile.kyc_status = 'Verified'  # Replace with real KYC integration in production
            profile.save()
            return Response({'message': 'KYC verified', 'user': UserProfileSerializer(profile).data}, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
