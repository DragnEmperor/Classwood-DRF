from rest_framework import serializers
from rest_framework.validators import ValidationError

from api.models import (
    Attachment,
    CommonTimeModel,
    ExamModel,
    ResultModel,
    SyllabusModel,
    TimeTableModel,
)

# ── Exams ──────────────────────────────────────────────────────────────────────


class ExamCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)

    class Meta:
        model = ExamModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]

        attachments = validated_data.pop("attachments", [])
        exam = ExamModel.objects.create(**validated_data)
        for f in attachments:
            att = Attachment.objects.create(fileName=f, school=validated_data["school"], attachType="exam")
            exam.attachments.add(att)
        return exam


class ExamListSerializer(serializers.ModelSerializer):
    attachments = serializers.StringRelatedField(many=True)
    subject_name = serializers.CharField(source="subject.name")
    classroom_name = serializers.SerializerMethodField()

    class Meta:
        model = ExamModel
        fields = "__all__"

    def get_classroom_name(self, obj):
        return f"{obj.classroom.class_name} - {obj.classroom.section_name}"


# ── Results ────────────────────────────────────────────────────────────────────


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultModel
        fields = "__all__"
        extra_kwargs = {
            "session": {"read_only": True},
        }

    def validate(self, attrs):
        score = attrs.get("score")
        exam = attrs.get("exam")
        if score is not None and exam and score > exam.max_marks:
            raise ValidationError({"score": "Score cannot exceed the exam's max marks."})
        return attrs

    def create(self, validated_data):
        validated_data["session"] = self.context["session"]
        return ResultModel.objects.create(**validated_data)


class ResultListSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    exam_tag = serializers.CharField(source="exam.tag")
    subject_name = serializers.CharField(source="exam.subject.name")
    classroom_name = serializers.SerializerMethodField()
    max_marks = serializers.IntegerField(source="exam.max_marks")
    date_of_exam = serializers.DateField(source="exam.date_of_exam")

    class Meta:
        model = ResultModel
        fields = "__all__"

    def get_student_name(self, obj):
        return obj.student.full_name

    def get_classroom_name(self, obj):
        return f"{obj.exam.classroom.class_name} - {obj.exam.classroom.section_name}"


# ── Syllabus ───────────────────────────────────────────────────────────────────


class SyllabusSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)

    class Meta:
        model = SyllabusModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]

        attachments = validated_data.pop("attachments", [])
        syllabus = SyllabusModel.objects.create(**validated_data)
        for f in attachments:
            att = Attachment.objects.create(fileName=f, school=validated_data["school"], attachType="syllabus")
            syllabus.attachments.add(att)
        return syllabus


class SyllabusListSerializer(serializers.ModelSerializer):
    attachments = serializers.StringRelatedField(many=True)
    subject_name = serializers.CharField(source="subject.name")
    classroom_name = serializers.SerializerMethodField()

    class Meta:
        model = SyllabusModel
        fields = "__all__"

    def get_classroom_name(self, obj):
        return f"{obj.classroom.class_name} - {obj.classroom.section_name}"


# ── Timetable ──────────────────────────────────────────────────────────────────


class TimeTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeTableModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]
        return super().create(validated_data)


class TimeTableListSerializer(serializers.ModelSerializer):
    subject = serializers.StringRelatedField()
    classroom = serializers.StringRelatedField()
    school = serializers.StringRelatedField()
    teacher = serializers.CharField(source="teacher.full_name")

    class Meta:
        model = TimeTableModel
        fields = "__all__"


class CommonTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonTimeModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]
        return super().create(validated_data)


class CommonTimeListSerializer(serializers.ModelSerializer):
    subject = serializers.StringRelatedField()
    classroom = serializers.StringRelatedField()
    school = serializers.StringRelatedField()

    class Meta:
        model = CommonTimeModel
        fields = "__all__"
