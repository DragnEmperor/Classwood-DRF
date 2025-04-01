from rest_framework import serializers

from api.models import StaffAttendance, StudentAttendance


class StudentAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAttendance
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def validate(self, attrs):
        student = attrs.get("student")
        classroom = attrs.get("classroom")
        if student and classroom and str(student.classroom_id) != str(classroom.pk):
            raise serializers.ValidationError({"classroom": "Classroom does not match the student's classroom."})
        return attrs

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]
        return super().create(validated_data)


class StudentAttendanceListSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField()
    classroom = serializers.StringRelatedField()
    school = serializers.StringRelatedField()

    class Meta:
        model = StudentAttendance
        fields = "__all__"


class StaffAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffAttendance
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]
        return super().create(validated_data)


class StaffAttendanceListSerializer(serializers.ModelSerializer):
    staff = serializers.StringRelatedField()
    school = serializers.StringRelatedField()

    class Meta:
        model = StaffAttendance
        fields = "__all__"
