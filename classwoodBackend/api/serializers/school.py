from rest_framework import serializers

from api.models import Accounts, SchoolModel, SessionModel
from api.serializers.accounts import AccountSerializer
from django.utils import timezone


class SchoolSignUpSerializer(serializers.ModelSerializer):
    user = AccountSerializer()

    class Meta:
        model = SchoolModel
        fields = "__all__"

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user = Accounts.objects.create_user(**user_data)
        school = SchoolModel.objects.create(user=user, **validated_data)
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=180)
        SessionModel.objects.create(school=school, start_date=start_date, end_date=end_date, is_active=True)
        return school


class SchoolProfileSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    student_strength = serializers.IntegerField(read_only=True)
    staff_strength = serializers.IntegerField(read_only=True)

    class Meta:
        model = SchoolModel
        fields = "__all__"


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        return SessionModel.objects.create(**validated_data)
