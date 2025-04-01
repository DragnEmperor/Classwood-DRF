from django.contrib.auth import get_user_model
from rest_framework import serializers

from api.models import Accounts

User = get_user_model()


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Accounts
        fields = ("id", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(min_length=8, max_length=20)
