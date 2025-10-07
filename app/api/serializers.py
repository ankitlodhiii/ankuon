from rest_framework import serializers
from ..models import UserProfile, Investment, Withdrawal


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'name', 'email', 'upi_id', 'kyc_status', 'verified']


class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = ['id', 'user', 'amount', 'order_id', 'status', 'returns', 'created_at']


class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = ['id', 'user', 'investment', 'amount', 'upi_id', 'processing_end', 'requested']
