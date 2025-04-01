from rest_framework import serializers
from decimal import Decimal
from api.models import FeesDetails, PaymentInfo


class FeesDetailsSerializer(serializers.ModelSerializer):
    className = serializers.SerializerMethodField()

    class Meta:
        model = FeesDetails
        fields = "__all__"
        extra_kwargs = {
            "school": {"read_only": True},
            "session": {"read_only": True},
        }

    def get_className(self, obj):
        return f"{obj.for_class.class_name} - {obj.for_class.section_name}"

    def create(self, validated_data):
        validated_data["school"] = self.context["school"]
        validated_data["session"] = self.context["session"]
        return super().create(validated_data)


class FeesListSerializer(serializers.ModelSerializer):
    className = serializers.SerializerMethodField()
    classroom_id = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()
    collection_status = serializers.SerializerMethodField()

    class Meta:
        model = FeesDetails
        fields = ["id", "fee_type", "amount", "className", "classroom_id", "due_date", "description", "created_at", "student_count", "collection_status"]

    def get_className(self, obj):
        return f"{obj.for_class.class_name} - {obj.for_class.section_name}"

    def get_classroom_id(self, obj):
        return obj.for_class.id

    def get_student_count(self, obj):
        return obj.for_class.studentmodel_set.count()

    def get_collection_status(self, obj):
        students_in_class = obj.for_class.studentmodel_set.all().count()
        payments = PaymentInfo.objects.filter(fees=obj)
        paid_students = payments.filter(amount_paid__gte=obj.amount).count()
        partial_payments = payments.filter(amount_paid__lt=obj.amount, amount_paid__gt=0).count()

        return {
            "total_students": students_in_class,
            "fully_paid": paid_students,
            "partially_paid": partial_payments,
            "outstanding": students_in_class - paid_students - partial_payments,
            "total_collected": str(sum(p.amount_paid for p in payments) or Decimal('0.00')),
            "collection_percentage": float((paid_students / students_in_class * 100) if students_in_class > 0 else 0)
        }


class PaymentInfoSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    fee_id = serializers.SerializerMethodField()
    fee_type = serializers.SerializerMethodField()
    fee_amount = serializers.SerializerMethodField()

    class Meta:
        model = PaymentInfo
        fields = ["id", "student_name", "fee_id", "fee_type", "fee_amount", "amount_paid", "payment_date", "payment_mode", "reference"]

    def get_student_name(self, obj):
        return obj.student.user.get_full_name()

    def get_fee_id(self, obj):
        return obj.fees_id

    def get_fee_type(self, obj):
        return obj.fees.fee_type

    def get_fee_amount(self, obj):
        return str(obj.fees.amount)


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentInfo
        fields = ["id", "student", "fees", "amount_paid", "payment_date", "payment_mode", "reference"]
