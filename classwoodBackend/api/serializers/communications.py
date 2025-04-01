from rest_framework import serializers

from api.models import Attachment, EventModel, Notice, ThoughtDayModel


class NoticeCreateSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)
    read_by_students = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    read_by_staff = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Notice
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]

        attachments = validated_data.pop("attachments", [])
        notice = Notice.objects.create(**validated_data)
        for f in attachments:
            att = Attachment.objects.create(fileName=f, school=validated_data["school"], attachType="notice")
            notice.attachments.add(att)
        return notice


class NoticeListSerializer(serializers.ModelSerializer):
    attachments = serializers.StringRelatedField(many=True)
    read_status = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = "__all__"

    def get_read_status(self, obj):
        user = self.context["request"].user
        return obj.read_by_students.filter(user=user).exists() or obj.read_by_staff.filter(user=user).exists()


class EventSerializer(serializers.ModelSerializer):
    attachments = serializers.ListField(child=serializers.FileField(), required=False, write_only=True)

    class Meta:
        model = EventModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]

        attachments = validated_data.pop("attachments", [])
        event = EventModel.objects.create(**validated_data)
        for f in attachments:
            att = Attachment.objects.create(fileName=f, school=validated_data["school"], attachType="events")
            event.attachments.add(att)
        return event


class EventListSerializer(serializers.ModelSerializer):
    attachments = serializers.StringRelatedField(many=True)

    class Meta:
        model = EventModel
        fields = "__all__"


class ThoughtDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ThoughtDayModel
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]
        return super().create(validated_data)
