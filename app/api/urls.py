from django.urls import path
from .views import (
    SendOTPView, VerifyOTPView, InvestView, CheckTransactionView,
    WithdrawView, CancelWithdrawalView, UpdateProfileView,
    KycVerificationView, ProfileView, CashfreeWebhookView,
    AdminLoginView, AdminStatsView, AdminSearchUsersView,
    AdminUserDetailView, AdminUserInvestmentsView, AdminUserWithdrawalsView,
    AdminPendingWithdrawalsView, AdminProcessWithdrawalView,
    AdminRejectWithdrawalView, AdminPendingBankTransfersView,
    AdminConfirmBankTransferView,
)

urlpatterns = [
    path('send-otp/', SendOTPView.as_view()),
    path('verify-otp/', VerifyOTPView.as_view()),
    path('profile/', ProfileView.as_view()),
    path('invest/', InvestView.as_view()),
    path('check-transaction/<str:order_id>/', CheckTransactionView.as_view()),
    path('withdraw/', WithdrawView.as_view()),
    path('cancel-withdrawal/', CancelWithdrawalView.as_view()),
    path('update-profile/', UpdateProfileView.as_view()),
    path('kyc-verification/', KycVerificationView.as_view()),
    path('webhooks/cashfree/', CashfreeWebhookView.as_view()),

    path('admin/login/', AdminLoginView.as_view()),
    path('admin/stats/', AdminStatsView.as_view()),
    path('admin/users/', AdminSearchUsersView.as_view()),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view()),
    path('admin/users/<int:user_id>/investments/', AdminUserInvestmentsView.as_view()),
    path('admin/users/<int:user_id>/withdrawals/', AdminUserWithdrawalsView.as_view()),
    path('admin/withdrawals/', AdminPendingWithdrawalsView.as_view()),
    path('admin/withdrawals/<int:withdrawal_id>/process/', AdminProcessWithdrawalView.as_view()),
    path('admin/withdrawals/<int:withdrawal_id>/reject/', AdminRejectWithdrawalView.as_view()),
    path('admin/investments/', AdminPendingBankTransfersView.as_view()),
    path('admin/investments/<int:investment_id>/confirm/', AdminConfirmBankTransferView.as_view()),
]
