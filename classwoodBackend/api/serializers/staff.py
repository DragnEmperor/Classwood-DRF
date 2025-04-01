from rest_framework import serializers

from api.models import StaffModel
from api.serializers.accounts import AccountSerializer
from api.utils import generate_staff_user


class StaffCreateSerializer(serializers.ModelSerializer):
    user = AccountSerializer(required=False, read_only=True)

    class Meta:
        model = StaffModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        school = self.context["school"]
        session = self.context["session"]
        validated_data["school"] = school
        validated_data["session"] = session

        user_data = generate_staff_user(
            validated_data["first_name"],
            validated_data["mobile_number"],
            validated_data["date_of_joining"],
        )
        from api.models import Accounts

        user = Accounts.objects.create_user(**user_data)
        return StaffModel.objects.create(user=user, **validated_data)


class StaffListSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    incharge_of = serializers.CharField()
    sub_incharge_of = serializers.StringRelatedField(many=True)
    gender = serializers.CharField(source="gender_display")
    total_attendance = serializers.FloatField()
    month_attendance = serializers.ListField()
    year_attendance = serializers.ListField()

    class Meta:
        model = StaffModel
        fields = "__all__"
