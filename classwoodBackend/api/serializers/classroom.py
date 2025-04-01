from rest_framework import serializers

from api.models import ClassroomModel, StaffModel, Subject


class ClassroomCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def validate_class_teacher(self, teacher):
        if teacher and teacher.is_class_teacher:
            raise serializers.ValidationError("This teacher is already assigned as a class teacher.")
        return teacher

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]

        teachers = [t for t in [validated_data.get("class_teacher"), validated_data.get("sub_class_teacher")] if t]
        classroom = ClassroomModel.objects.create(**validated_data)
        classroom.teachers.set(teachers)

        # Mark the class teacher
        class_teacher = validated_data.get("class_teacher")
        if class_teacher:
            StaffModel.objects.filter(user=class_teacher.user).update(is_class_teacher=True)

        return classroom


class ClassroomListSerializer(serializers.ModelSerializer):
    strength = serializers.CharField()
    no_of_subjects = serializers.SerializerMethodField()
    no_of_teachers = serializers.SerializerMethodField()
    teachers = serializers.StringRelatedField(many=True)
    class_teacher = serializers.SerializerMethodField()
    sub_class_teacher = serializers.SerializerMethodField()

    class Meta:
        model = ClassroomModel
        fields = "__all__"

    def get_no_of_subjects(self, obj):
        return str(obj.no_of_subjects)

    def get_no_of_teachers(self, obj):
        return str(obj.no_of_teachers)

    def get_class_teacher(self, obj):
        if obj.class_teacher is None:
            return "not assigned"
        return obj.class_teacher.full_name

    def get_sub_class_teacher(self, obj):
        if obj.sub_class_teacher is None:
            return "not assigned"
        return obj.sub_class_teacher.full_name


class SubjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]

        teacher = validated_data.get("teacher")
        classroom = validated_data.get("classroom")

        subject = Subject.objects.create(**validated_data)

        # Add the teacher to the classroom's teachers list
        if teacher and classroom:
            classroom.teachers.add(teacher)

        return subject


class SubjectListSerializer(serializers.ModelSerializer):
    classroom_name = serializers.SerializerMethodField()
    teacher = serializers.SerializerMethodField(method_name="get_teacher_name")
    teacher_id = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = "__all__"

    def get_teacher_name(self, obj):
        if obj.teacher is None:
            return "not assigned"
        return obj.teacher.full_name

    def get_teacher_id(self, obj):
        if obj.teacher is None:
            return "not assigned"
        return obj.teacher.user_id

    def get_classroom_name(self, obj):
        return f"{obj.classroom.class_name}-{obj.classroom.section_name}"
