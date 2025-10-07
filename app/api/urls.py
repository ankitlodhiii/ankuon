# app/api/urls.py
from django.urls import path
from .views import SendOTPView, VerifyOTPView, InvestView, CheckTransactionView, WithdrawView, CancelWithdrawalView, UpdateProfileView, KycVerificationView

urlpatterns = [
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('invest/', InvestView.as_view(), name='invest'),
    path('check-transaction/<str:order_id>/', CheckTransactionView.as_view(), name='check-transaction'),
    path('withdraw/', WithdrawView.as_view(), name='withdraw'),
    path('cancel-withdrawal/', CancelWithdrawalView.as_view(), name='cancel-withdrawal'),
    path('update-profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('kyc-verification/', KycVerificationView.as_view(), name='kyc-verification'),
]
