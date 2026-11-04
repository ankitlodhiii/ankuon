
from rest_framework import serializers

from .models import (
    UserProfile,
    Kyc,
    Investment,
    Withdrawal,
    SecurityLog,
    FocusItem,
    CoreSkill,
    LifeGoal,
    CustomGoal,
    Emi,
    Receivable,
    Payable,
    MoneyRule,
    MindsetPoint,
    IncomeSource,
    RoutineRow,
    Skill,
    GitaShloka,
    Journal,
    Note,
    Balance,
    Setting,
)


# =====================================================
# USER PROFILE
# =====================================================

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"
        read_only_fields = [
            "id",
            "user",
            "kyc_status",
            "verified",
            "created_at",
            "last_login",
        ]


# =====================================================
# KYC
# =====================================================

class KycSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kyc
        fields = "__all__"
        read_only_fields = [
            "id",
            "profile",
            "verified_at",
        ]


# =====================================================
# INVESTMENT
# =====================================================

class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = "__all__"
        read_only_fields = [
            "id",
            "profile",
            "date",
            "returns",
            "order_id",
            "status",
            "virtual_account",
            "confirmed_at",
        ]


# =====================================================
# WITHDRAWAL
# =====================================================

class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = "__all__"
        read_only_fields = [
            "id",
            "profile",
            "requested",
            "status",
            "processing_end",
            "utr",
        ]


# =====================================================
# SECURITY LOG
# =====================================================

class SecurityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityLog
        fields = "__all__"
        read_only_fields = [
            "id",
            "profile",
            "at",
        ]


# =====================================================
# PERSONAL PANEL SERIALIZERS
# =====================================================

class FocusItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FocusItem
        fields = ["id", "text", "created_at"]
        read_only_fields = ["id", "created_at"]


class CoreSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoreSkill
        fields = ["id", "text", "created_at"]
        read_only_fields = ["id", "created_at"]


class LifeGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = LifeGoal
        fields = ["id", "text", "created_at"]
        read_only_fields = ["id", "created_at"]


class CustomGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomGoal
        fields = ["id", "text", "done", "created_at"]
        read_only_fields = ["id", "created_at"]


class EmiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emi
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at"]


class ReceivableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receivable
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at"]


class PayableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payable
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at"]


class MoneyRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoneyRule
        fields = ["id", "text", "created_at"]
        read_only_fields = ["id", "created_at"]


class MindsetPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = MindsetPoint
        fields = ["id", "text", "created_at"]
        read_only_fields = ["id", "created_at"]


class IncomeSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeSource
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at"]


class RoutineRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutineRow
        fields = [
            "id",
            "time",
            "activity",
            "duration",
            "order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = [
            "id",
            "text",
            "hours",
            "target",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class GitaShlokaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitaShloka
        fields = [
            "id",
            "sanskrit",
            "eng",
            "hin",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = [
            "id",
            "date",
            "happened",
            "feel",
            "learn",
            "want",
            "promise",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "content", "updated_at"]
        read_only_fields = ["id", "updated_at"]


class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = ["id", "sbi", "punb", "inv"]
        read_only_fields = ["id"]


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = [
            "id",
            "mission_end_date",
            "jaap_today",
            "jaap_date",
            "monthly_need",
            "finance_notes",
            "skills_notes",
        ]
        read_only_fields = ["id"]
