from rest_framework import serializers

from api.models import StudentModel, Subject
from api.serializers.accounts import AccountSerializer
from api.utils import generate_staff_user


class StudentCreateSerializer(serializers.ModelSerializer):
    user = AccountSerializer(required=False, read_only=True)

    class Meta:
        model = StudentModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def validate_subjects(self, subjects):
        """Ensure all subjects belong to the student's classroom."""
        classroom = self.initial_data.get("classroom")
        for subject in subjects:
            if str(subject.classroom_id) != str(classroom):
                raise serializers.ValidationError(
                    f"Subject '{subject.name}' does not belong to the selected classroom."
                )
        return subjects

    def create(self, validated_data):
        school = self.context["school"]
        session = self.context["session"]
        validated_data["school"] = school
        validated_data["session"] = session

        subjects = validated_data.pop("subjects", [])
        user_data = generate_staff_user(
            validated_data["first_name"],
            validated_data.get("parent_mobile_number", ""),
            validated_data["date_of_admission"],
        )
        from api.models import Accounts

        user = Accounts.objects.create_user(**user_data)
        instance = StudentModel.objects.create(user=user, **validated_data)

        if subjects:
            instance.subjects.set(subjects)
        else:
            # Default: assign all subjects for the classroom
            classroom = validated_data.get("classroom")
            if classroom:
                default_subjects = Subject.objects.filter(classroom=classroom, session=session)
                instance.subjects.set(default_subjects)

        return instance


class StudentListSerializer(serializers.ModelSerializer):
    user = AccountSerializer()
    subjects = serializers.StringRelatedField(many=True)
    classroom = serializers.StringRelatedField()
    gender = serializers.CharField(source="gender_display")
    total_attendance = serializers.FloatField()
    month_attendance = serializers.ListField()
    year_attendance = serializers.ListField()

    class Meta:
        model = StudentModel
        fields = "__all__"
