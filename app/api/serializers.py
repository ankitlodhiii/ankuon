from rest_framework import serializers
from app.models import UserProfile, Investment, Withdrawal, Kyc


class KycSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kyc
        fields = [
            'pan', 'aadhaar', 'mobile', 'account_name',
            'bank_account', 'ifsc', 'banks',
            'aadhaar_mobile_linked', 'verified_at'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    kyc = KycSerializer(read_only=True)
    kycData = serializers.SerializerMethodField()
    kycStatus = serializers.CharField(source='kyc_status')
    twoFactorEnabled = serializers.BooleanField(source='two_factor_enabled')
    lastLogin = serializers.DateTimeField(source='last_login')
    investments = serializers.SerializerMethodField()
    withdrawals = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'email', 'name', 'upi_id', 'mobile', 'kycStatus',
            'verified', 'twoFactorEnabled', 'lastLogin',
            'kyc', 'kycData', 'investments', 'withdrawals'
        ]

    def get_kycData(self, obj):
        if hasattr(obj, 'kyc') and obj.kyc:
            return KycSerializer(obj.kyc).data
        return None

    def get_investments(self, obj):
        return InvestmentSerializer(obj.investments.all().order_by('-date'), many=True).data

    def get_withdrawals(self, obj):
        return WithdrawalSerializer(obj.withdrawals.all().order_by('-requested'), many=True).data


class InvestmentSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField()
    class Meta:
        model = Investment
        fields = [
            'id', 'amount', 'date', 'returns', 'order_id',
            'status', 'payment_method', 'virtual_account', 'confirmed_at'
        ]


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = [
            'id', 'investment_id', 'amount', 'requested', 'status',
            'processing_end', 'bank_account', 'ifsc', 'account_name',
            'method', 'utr', 'notes'
        ]
