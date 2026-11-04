
from django.urls import path

from .views import (
    SendOTPView,
    VerifyOTPView,
    InvestView,
    CheckTransactionView,
    WithdrawView,
    CancelWithdrawalView,
    UpdateProfileView,
    KycVerificationView,
    ProfileView,
    CashfreeWebhookView,
    AdminLoginView,
    AdminStatsView,
    AdminSearchUsersView,
    AdminUserDetailView,
    AdminUserInvestmentsView,
    AdminUserWithdrawalsView,
    AdminPendingWithdrawalsView,
    AdminProcessWithdrawalView,
    AdminRejectWithdrawalView,
    AdminPendingBankTransfersView,
    AdminConfirmBankTransferView,
)


# =====================================================
# USER AUTHENTICATION & PROFILE
# =====================================================

urlpatterns = [
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("update-profile/", UpdateProfileView.as_view(), name="update-profile"),

    # =================================================
    # INVESTMENT
    # =================================================

    path("invest/", InvestView.as_view(), name="invest"),
    path(
        "check-transaction/<str:order_id>/",
        CheckTransactionView.as_view(),
        name="check-transaction",
    ),

    # =================================================
    # WITHDRAWAL
    # =================================================

    path("withdraw/", WithdrawView.as_view(), name="withdraw"),
    path(
        "cancel-withdrawal/",
        CancelWithdrawalView.as_view(),
        name="cancel-withdrawal",
    ),

    # =================================================
    # KYC
    # =================================================

    path(
        "kyc-verification/",
        KycVerificationView.as_view(),
        name="kyc-verification",
    ),

    # =================================================
    # CASHFREE WEBHOOK
    # =================================================

    path(
        "webhooks/cashfree/",
        CashfreeWebhookView.as_view(),
        name="cashfree-webhook",
    ),

    # =================================================
    # ADMIN AUTHENTICATION & DASHBOARD
    # =================================================

    path("admin/login/", AdminLoginView.as_view(), name="admin-login"),
    path("admin/stats/", AdminStatsView.as_view(), name="admin-stats"),

    # =================================================
    # ADMIN USER MANAGEMENT
    # =================================================

    path("admin/users/", AdminSearchUsersView.as_view(), name="admin-users"),
    path(
        "admin/users/<int:user_id>/",
        AdminUserDetailView.as_view(),
        name="admin-user-detail",
    ),
    path(
        "admin/users/<int:user_id>/investments/",
        AdminUserInvestmentsView.as_view(),
        name="admin-user-investments",
    ),
    path(
        "admin/users/<int:user_id>/withdrawals/",
        AdminUserWithdrawalsView.as_view(),
        name="admin-user-withdrawals",
    ),

    # =================================================
    # ADMIN WITHDRAWAL MANAGEMENT
    # =================================================

    path(
        "admin/withdrawals/",
        AdminPendingWithdrawalsView.as_view(),
        name="admin-pending-withdrawals",
    ),
    path(
        "admin/withdrawals/<int:withdrawal_id>/process/",
        AdminProcessWithdrawalView.as_view(),
        name="admin-process-withdrawal",
    ),
    path(
        "admin/withdrawals/<int:withdrawal_id>/reject/",
        AdminRejectWithdrawalView.as_view(),
        name="admin-reject-withdrawal",
    ),

    # =================================================
    # ADMIN BANK TRANSFER MANAGEMENT
    # =================================================

    path(
        "admin/investments/",
        AdminPendingBankTransfersView.as_view(),
        name="admin-pending-investments",
    ),
    path(
        "admin/investments/<int:investment_id>/confirm/",
        AdminConfirmBankTransferView.as_view(),
        name="admin-confirm-investment",
    ),
]
