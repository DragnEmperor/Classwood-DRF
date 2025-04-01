import datetime

import pyotp
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api import serializers
from api.mixins import SchoolContextMixin
from api.models import (
    OTPModel,
    SchoolModel,
    SessionModel,
    StaffModel,
    ThoughtDayModel,
    PaymentInfo,
    FeesDetails,
    StudentModel,
)
from api.permissions import (
    AdminPermission,
    IsTokenValid,
    ReadOnlyStaffPermission,
    ReadOnlyStudentPermission,
)
from api.services import import_staff_from_csv

User = get_user_model()


# ── Auth / Profile ─────────────────────────────────────────────────────────────


class SchoolSignUpView(generics.CreateAPIView):
    serializer_class = serializers.SchoolSignUpSerializer
    permission_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "School User Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = serializers.ForgotPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()
        if not user or not SchoolModel.objects.filter(user=user).exists():
            return Response({"message": "No School Account associated with this email found"})

        otp_base = pyotp.random_base32()
        otp_code = pyotp.TOTP(otp_base, digits=6).now()
        OTPModel.objects.create(
            email=email,
            hashed_otp=make_password(otp_code),
            expiration_time=timezone.now() + datetime.timedelta(minutes=5),
        )

        send_mail(
            "Forgot Password - ClassWood",
            f"Use the following OTP to reset your password: {otp_code}\n\nValid for 5 minutes.",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return Response({"message": "An OTP to reset your password has been sent to your email."})


class VerifyOTPView(generics.GenericAPIView):
    serializer_class = serializers.VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["password"]

        otp_obj = OTPModel.objects.filter(email=email).last()
        if not otp_obj or not check_password(otp, otp_obj.hashed_otp) or otp_obj.expiration_time < timezone.now():
            return Response({"message": "Invalid OTP! Please Try Again"})

        otp_obj.delete()
        user = get_object_or_404(User, email=email)
        user.set_password(new_password)
        user.save(update_fields=["password"])

        send_mail(
            "Password Changed - ClassWood",
            "Your password has been changed. If not done by you, contact admin.",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return Response({"message": "Password Changed Successfully"})


class SchoolProfileView(SchoolContextMixin, generics.RetrieveUpdateAPIView):
    serializer_class = serializers.SchoolProfileSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]

    def get_object(self):
        school = get_object_or_404(SchoolModel, user=self.request.user)
        school.user.password = None
        return school

    def patch(self, request, *args, **kwargs):
        school = self.get_object()
        serializer = self.get_serializer(school, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── Staff ──────────────────────────────────────────────────────────────────────


class StaffView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.StaffCreateSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]
    queryset = StaffModel.objects.all()

    def get_queryset(self):
        school = self.get_school()
        session = self.get_active_session(school)
        qs = StaffModel.objects.filter(school=school, session=session)
        for s in qs:
            s.user.password = None
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.StaffListSerializer
        return self.serializer_class

    def destroy(self, request, *args, **kwargs):
        from api.models import Accounts

        account = get_object_or_404(Accounts, id=self.kwargs["pk"])
        account.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        csv_file = request.FILES.get("csv_file")
        if csv_file:
            school = self.get_school()
            session = self.get_active_session(school)
            created, errors = import_staff_from_csv(csv_file, school, session)
            if errors:
                return Response(errors, status=status.HTTP_200_OK)
            return Response({"message": "Staff Added from CSV Successfully"}, status=status.HTTP_201_CREATED)

        # Single create — delegates to serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Staff Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

# ── Student ──────────────────────────────────────────────────────────────────────

class StudentListView(SchoolContextMixin, generics.ListAPIView):
    serializer_class = serializers.StudentListSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]

    def get_queryset(self):
        school = self.get_school()
        session = self.get_active_session(school)
        students = StudentModel.objects.filter(school=school, session=session)
        for s in students:
            s.user.password = None
        return students


# ── Classrooms ─────────────────────────────────────────────────────────────────


class ClassroomSchoolView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.ClassroomCreateSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]
    queryset = SchoolModel.objects.none()

    def get_queryset(self):
        from api.models import ClassroomModel

        school = self.get_school()
        session = self.get_active_session(school)
        return ClassroomModel.objects.filter(school=school, session=session)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.ClassroomListSerializer
        return serializers.ClassroomCreateSerializer

    def destroy(self, request, *args, **kwargs):
        from api.models import ClassroomModel

        classroom = ClassroomModel.objects.get(id=self.kwargs["pk"])
        StaffModel.objects.filter(user=classroom.class_teacher).update(is_class_teacher=False)
        classroom.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Classroom Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ── Notices ────────────────────────────────────────────────────────────────────


class NoticeView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.NoticeCreateSerializer
    permission_classes = [
        IsAuthenticated & (ReadOnlyStaffPermission | ReadOnlyStudentPermission | AdminPermission) & IsTokenValid
    ]

    def get_queryset(self):
        from api.models import Notice

        school = self.get_school()
        session = self.get_active_session(school)
        return Notice.objects.filter(school=school, session=session)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.NoticeListSerializer
        return self.serializer_class

    def get_object(self):
        from api.models import StudentModel

        notice = super().get_object()
        user = self.request.user

        try:
            student = StudentModel.objects.get(user=user)
            notice.read_by_students.add(student)
        except StudentModel.DoesNotExist:
            try:
                staff = StaffModel.objects.get(user=user)
                notice.read_by_staff.add(staff)
            except StaffModel.DoesNotExist:
                pass
        return notice

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Notice Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ── Events ─────────────────────────────────────────────────────────────────────


class EventView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.EventSerializer
    permission_classes = [
        IsAuthenticated & (ReadOnlyStaffPermission | ReadOnlyStudentPermission | AdminPermission) & IsTokenValid
    ]

    def get_queryset(self):
        from api.models import EventModel

        school = self.get_school()
        return EventModel.objects.filter(school=school)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.EventListSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Event Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ── Attendance (Staff) ────────────────────────────────────────────────────────


class StaffAttendanceView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.StaffAttendanceSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]

    def get_queryset(self):
        from api.models import StaffAttendance

        school = self.get_school()
        return StaffAttendance.objects.filter(school=school)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.StaffAttendanceListSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Staff Attendance Marked Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ── Sessions ───────────────────────────────────────────────────────────────────


class SessionView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.SessionSerializer
    permission_classes = [IsAuthenticated & (AdminPermission | ReadOnlyStaffPermission) & IsTokenValid]

    def get_queryset(self):
        school = self.get_school()
        # Deactivate any expired active sessions
        active = SessionModel.objects.filter(school=school, is_active=True)
        for s in active:
            s.deactivate_if_expired()
        return SessionModel.objects.filter(school=school).order_by("-is_active", "-start_date")

    def create(self, request, *args, **kwargs):
        school = self.get_school()
        active_count = SessionModel.objects.filter(school=school, is_active=True).count()
        if active_count >= 2:
            return Response(
                {"message": "More than two active sessions not allowed."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Session Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ── Thought of the Day ────────────────────────────────────────────────────────


class ThoughtsView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.ThoughtDaySerializer
    permission_classes = [
        IsAuthenticated & (AdminPermission | ReadOnlyStaffPermission | ReadOnlyStudentPermission) & IsTokenValid
    ]

    def get_queryset(self):
        school = self.get_school()
        session = self.get_active_session(school)
        return ThoughtDayModel.objects.filter(school=school, session=session)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Thought of the Day Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ── Fees ───────────────────────────────────────────────────────────────────────


class FeesDetailsView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.FeesDetailsSerializer
    permission_classes = [
        IsAuthenticated & (AdminPermission | ReadOnlyStaffPermission | ReadOnlyStudentPermission) & IsTokenValid
    ]

    def get_queryset(self):
        from api.models import FeesDetails

        school = self.get_school()
        session = self.get_active_session(school)
        classroom = self.request.query_params.get("classroom")

        qs = FeesDetails.objects.filter(school=school, session=session).order_by("-created_at")
        if classroom:
            qs = qs.filter(for_class=classroom)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.FeesListSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        from api.models import StudentModel

        data = request.data.copy()
        student_data = data.pop("student_data", [])
        fee_data = data.pop("fee_data", [])

        # Update student waivers
        for entry in student_data:
            stud_user = entry.get("user", {})
            concession = entry.get("concession", {})
            try:
                student = StudentModel.objects.get(user=stud_user.get("id"))
                student.waiver_type = concession.get("title", "none")
                student.waiver_percent = int(concession.get("value", 0)) / 100
                student.save(update_fields=["waiver_type", "waiver_percent"])
            except StudentModel.DoesNotExist:
                continue

        # Create fee records
        errors = []
        for idx, fee in enumerate(fee_data, 1):
            ser = self.get_serializer(
                data={"amount": fee.get("fees"), "fee_type": fee.get("title"), "for_class": data.get("for_class")}
            )
            if ser.is_valid():
                ser.save()
            else:
                errors.append({"row": idx, "errors": ser.errors})

        if errors:
            return Response(errors, status=status.HTTP_200_OK)
        return Response({"message": "Fees Added Successfully"}, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        summary = request.query_params.get("summary")

        if summary == "true":
            school = self.get_school()
            session = self.get_active_session(school)

            fees = FeesDetails.objects.filter(school=school, session=session)
            total_fees = sum(fee.amount for fee in fees)

            payments = PaymentInfo.objects.filter(fees__school=school, fees__session=session)
            total_paid = sum(payment.amount_paid for payment in payments)

            pending = total_fees - total_paid

            return Response({
                "total_fees": str(total_fees),
                "total_paid": str(total_paid),
                "pending": str(pending),
                "paid_percentage": float((total_paid / total_fees * 100) if total_fees > 0 else 0)
            })
        return super().list(request, *args, **kwargs)


class PaymentHistoryView(SchoolContextMixin, generics.ListCreateAPIView):
    serializer_class = serializers.PaymentInfoSerializer
    permission_classes = [IsAuthenticated & (AdminPermission | ReadOnlyStaffPermission) & IsTokenValid]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.PaymentCreateSerializer
        return self.serializer_class

    def get_queryset(self):
        school = self.get_school()
        session = self.get_active_session(school)
        return PaymentInfo.objects.filter(fees__school=school, fees__session=session).order_by("-payment_date")

    def list(self, request, *args, **kwargs):
        limit = request.query_params.get("limit")

        queryset = self.get_queryset()

        if limit and limit.isdigit():
            queryset = queryset[: int(limit)]

        serializer = self.get_serializer(queryset, many=True)
        return Response({"payments": serializer.data, "count": queryset.count()})
