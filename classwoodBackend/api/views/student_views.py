import datetime

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api import serializers
from api.mixins import SchoolContextMixin
from api.models import (
    FeesDetails,
    PaymentInfo,
    ResultModel,
    StudentModel,
    Subject,
    SyllabusModel,
    ThoughtDayModel,
)
from api.permissions import (
    AdminPermission,
    IsTokenValid,
    StaffLevelPermission,
    StudentLevelPermission,
)


class StudentSingleView(SchoolContextMixin, generics.RetrieveUpdateAPIView):
    serializer_class = serializers.StudentListSerializer
    permission_classes = [
        IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid
    ]

    def get_object(self):
        student = StudentModel.objects.get(user=self.request.user)
        student.user.password = None
        return student

    def patch(self, request, *args, **kwargs):
        data = request.data
        if "user" in data:
            return Response({"message": "Account credentials cannot be changed. Contact Administrator."})
        if "school" in data:
            return Response({"message": "School cannot be changed. Contact Administrator."})

        student = self.get_object()
        serializer = self.get_serializer(student, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentSubjectView(SchoolContextMixin, generics.ListAPIView):
    serializer_class = serializers.SubjectListSerializer
    permission_classes = [
        IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid
    ]

    def get_queryset(self):
        session = self.get_active_session(self.get_school())
        student = StudentModel.objects.get(user=self.request.user, session=session)
        return Subject.objects.filter(classroom=student.classroom, school=student.school, session=session)


class StudentSyllabusView(SchoolContextMixin, generics.ListAPIView):
    serializer_class = serializers.SyllabusListSerializer
    permission_classes = [
        IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid
    ]

    def get_queryset(self):
        student = StudentModel.objects.get(user=self.request.user)
        return SyllabusModel.objects.filter(
            subject__classroom=student.classroom,
            subject__school=student.school,
        )


class StudentResultView(SchoolContextMixin, generics.ListAPIView):
    serializer_class = serializers.ResultListSerializer
    permission_classes = [
        IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid
    ]

    def get_queryset(self):
        student = StudentModel.objects.get(user=self.request.user)
        exam_id = self.request.query_params.get("exam")
        qs = ResultModel.objects.filter(student=student)
        if exam_id:
            qs = qs.filter(exam_id=exam_id)
        return qs


class ThoughtOfDayView(SchoolContextMixin, generics.RetrieveAPIView):
    serializer_class = serializers.ThoughtDaySerializer
    permission_classes = [
        IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid
    ]

    def get_object(self):
        date = self.request.query_params.get("date", datetime.date.today())
        return ThoughtDayModel.objects.get(date=date)


class FeeStudentView(SchoolContextMixin, generics.RetrieveAPIView):
    permission_classes = [
        IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid
    ]

    def get(self, request, *args, **kwargs):
        student = StudentModel.objects.get(user=request.user)
        fees = FeesDetails.objects.filter(for_class=student.classroom)
        total = sum(f.amount for f in fees)
        payable = total - (total * student.waiver_percent)
        payments = PaymentInfo.objects.filter(student=student, fees__in=fees).select_related("fees")
        total_paid = sum(payment.amount_paid for payment in payments)
        balance = payable - total_paid
        return Response(
            {
                "fees": serializers.FeesDetailsSerializer(fees, many=True).data,
                "payments": serializers.PaymentInfoSerializer(payments, many=True).data,
                "total_amount": str(total),
                "amount_to_pay": str(payable),
                "total_paid": str(total_paid),
                "balance_due": str(balance if balance > 0 else 0),
            }
        )
