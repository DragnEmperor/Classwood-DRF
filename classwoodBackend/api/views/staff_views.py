from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api import serializers
from api.mixins import SchoolContextMixin
from api.models import (
    ClassroomModel,
    ExamModel,
    StaffModel,
    Subject,
)
from api.permissions import (
    AdminPermission,
    IsTokenValid,
    ReadOnlyStaffPermission,
    ReadOnlyStudentPermission,
    StaffLevelPermission,
)
from api.services import import_results_from_csv, import_students_from_csv

# ── Staff Profile ──────────────────────────────────────────────────────────────


class StaffSingleView(SchoolContextMixin, generics.RetrieveUpdateAPIView):
    serializer_class = serializers.StaffListSerializer
    permission_classes = [IsAuthenticated & StaffLevelPermission & ~AdminPermission & IsTokenValid]

    def get_object(self):
        staff = StaffModel.objects.get(user=self.request.user)
        staff.user.password = None
        return staff

    def patch(self, request, *args, **kwargs):
        data = request.data
        if "user" in data:
            return Response({"message": "Account credentials cannot be changed. Contact Administrator."})
        if "school" in data:
            return Response({"message": "School cannot be changed. Contact Administrator."})

        staff = self.get_object()
        serializer = self.get_serializer(staff, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── Classrooms (Staff view — read-only) ───────────────────────────────────────


class ClassroomStaffView(SchoolContextMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.ClassroomCreateSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = ClassroomModel.objects.none()

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.ClassroomListSerializer
        return self.serializer_class

    def get_queryset(self):
        school = self.get_school()
        session = self.get_active_session(school)
        teacher = get_object_or_404(StaffModel, user=self.request.user)

        assigned = ClassroomModel.objects.filter(
            Q(class_teacher=teacher) | Q(sub_class_teacher=teacher),
            session=session,
        )
        teaches_ids = Subject.objects.filter(teacher=teacher).values_list("classroom", flat=True)
        taught = ClassroomModel.objects.filter(id__in=teaches_ids, session=session)

        return (assigned | taught).distinct()


# ── Subjects ───────────────────────────────────────────────────────────────────


class SubjectCreateView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.SubjectCreateSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = Subject.objects.none()

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.SubjectListSerializer
        return self.serializer_class

    def get_queryset(self):
        school = self.get_school()
        session = self.get_active_session(school)
        classroom_id = self.request.query_params.get("classroom")

        # If user is a teacher, scope to their classrooms
        is_teacher = StaffModel.objects.filter(user=self.request.user, session=session).exists()
        qs = Subject.objects.filter(school=school, session=session)

        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)

        if is_teacher:
            teacher = StaffModel.objects.get(user=self.request.user, session=session)
            own_classrooms = ClassroomModel.objects.filter(Q(class_teacher=teacher) | Q(sub_class_teacher=teacher))
            # If requesting a specific classroom they're in charge of, show all subjects
            if classroom_id and own_classrooms.filter(id=classroom_id).exists():
                return qs
            # Otherwise only their subjects
            qs = qs.filter(teacher=teacher)

        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Subject Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ── Students ───────────────────────────────────────────────────────────────────


class StudentListCreateView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.StudentCreateSerializer
    permission_classes = [(ReadOnlyStaffPermission | AdminPermission) & IsAuthenticated & IsTokenValid]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = StaffModel.objects.none()  # placeholder; overridden by get_queryset

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.StudentListSerializer
        return self.serializer_class

    def get_queryset(self):
        from django.db.models import Prefetch
        from django.utils import timezone
        from api.models import StudentAttendance, StudentModel

        school = self.get_school()
        session = self.get_active_session(school)
        classroom_id = self.request.query_params.get("classroom")

        year_attendance = StudentAttendance.objects.filter(date__year=timezone.now().year).order_by("date")

        qs = (
            StudentModel.objects.filter(school=school, session=session)
            .select_related("user", "classroom")
            .prefetch_related("subjects", Prefetch("studentattendance_set", queryset=year_attendance))
        )
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        for s in qs:
            s.user.password = None
        return qs

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
            classroom_id = request.data.get("classroom")
            created, errors = import_students_from_csv(csv_file, school, session, classroom_id)
            if errors:
                return Response(errors, status=status.HTTP_200_OK)
            return Response({"message": "Students Added from CSV Successfully"}, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Student Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        from api.utils import generate_staff_user

        student = self.get_object()
        data = request.data.copy()

        # Re-generate credentials if key fields changed
        new_name = data.get("first_name", student.first_name)
        new_phone = data.get("parent_mobile_number", student.parent_mobile_number)
        new_doa = data.get("date_of_admission", student.date_of_admission)
        if new_name != student.first_name or new_phone != student.parent_mobile_number:
            creds = generate_staff_user(new_name, new_phone, new_doa)
            user = student.user
            user.email = creds["email"]
            user.set_password(creds["password"])
            user.save()

        serializer = self.get_serializer(student, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# ── Student Attendance ─────────────────────────────────────────────────────────


class StudentAttendanceView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.StudentAttendanceSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]

    def get_queryset(self):
        from api.models import StudentAttendance

        school = self.get_school()
        session = self.get_active_session(school)
        classroom_id = self.request.query_params.get("classroom")

        qs = StudentAttendance.objects.filter(school=school, session=session)
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.StudentAttendanceListSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Student Attendance Marked Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ── Exams ──────────────────────────────────────────────────────────────────────


class ExamView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.ExamCreateSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]

    def get_queryset(self):
        school = self.get_school()
        session = self.get_active_session(school)
        classroom_id = self.request.query_params.get("classroom")

        qs = ExamModel.objects.filter(school=school, session=session)
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.ExamListSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Exam Added Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class ExamMarkView(generics.UpdateAPIView):
    queryset = ExamModel.objects.all()

    def patch(self, request, *args, **kwargs):
        exam = self.get_object()
        exam.is_complete = request.data.get("is_complete", exam.is_complete)
        exam.save(update_fields=["is_complete"])
        return JsonResponse({"exam": model_to_dict(exam), "message": "Exam Marked Successfully"})


# ── Results ────────────────────────────────────────────────────────────────────


class ResultView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.ResultSerializer
    permission_classes = [
        IsAuthenticated & (StaffLevelPermission | AdminPermission | ReadOnlyStudentPermission) & IsTokenValid
    ]

    def get_queryset(self):
        from api.models import ResultModel

        school = self.get_school()
        session = self.get_active_session(school)
        qs = ResultModel.objects.filter(student__school=school, session=session)

        student_id = self.request.query_params.get("student")
        exam_id = self.request.query_params.get("exam")
        if student_id:
            qs = qs.filter(student_id=student_id)
        if exam_id:
            qs = qs.filter(exam_id=exam_id)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.ResultListSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        csv_file = request.FILES.get("csv_file")
        if csv_file:
            school = self.get_school()
            session = self.get_active_session(school)
            created, errors = import_results_from_csv(
                csv_file,
                school,
                session,
                exam_id=request.data.get("exam"),
                classroom_id=request.data.get("classroom"),
            )
            if errors:
                return Response(errors, status=status.HTTP_200_OK)
            return Response({"message": "Results Added from CSV Successfully"}, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Result Created Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


# ── Timetable ──────────────────────────────────────────────────────────────────


class TimeTableView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.TimeTableSerializer
    permission_classes = [
        IsAuthenticated & (ReadOnlyStaffPermission | ReadOnlyStudentPermission | AdminPermission) & IsTokenValid
    ]

    def get_queryset(self):
        from api.models import TimeTableModel

        school = self.get_school()
        session = self.get_active_session(school)
        classroom_id = self.request.query_params.get("classroom")

        qs = TimeTableModel.objects.filter(school=school, session=session)
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.TimeTableListSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        timetable = request.data.get("timetable")
        classroom_id = request.data.get("classroom")

        if not timetable or not classroom_id:
            return Response({"message": "Timetable and classroom are required."}, status=status.HTTP_400_BAD_REQUEST)

        errors = []
        for day_idx in range(6):
            for slot in timetable[day_idx]:
                subject_info = slot.get("subject", {})
                if subject_info.get("name") == "No Subject Selected":
                    continue

                entry = {
                    "day": day_idx,
                    "start_time": f"{slot['start']['hour']}:{slot['start']['minute']}:00",
                    "end_time": f"{slot['end']['hour']}:{slot['end']['minute']}:00",
                    "subject": subject_info.get("id"),
                    "teacher": subject_info.get("teacher_id"),
                    "classroom": classroom_id,
                }
                serializer = self.get_serializer(data=entry)
                if serializer.is_valid():
                    serializer.save()
                else:
                    errors.append({"row": day_idx, "errors": serializer.errors})

        if errors:
            return Response(errors, status=status.HTTP_200_OK)
        return Response({"message": "Timetable Added Successfully"}, status=status.HTTP_201_CREATED)


# ── Common Time ────────────────────────────────────────────────────────────────


class CommonTimeView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.CommonTimeSerializer
    permission_classes = [
        IsAuthenticated & (ReadOnlyStaffPermission | ReadOnlyStudentPermission | AdminPermission) & IsTokenValid
    ]

    def get_queryset(self):
        from api.models import CommonTimeModel

        school = self.get_school()
        session = self.get_active_session(school)
        classroom_id = self.request.query_params.get("classroom")

        qs = CommonTimeModel.objects.filter(school=school, session=session)
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.CommonTimeListSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        classroom_id = request.data.get("classroom")
        if not classroom_id:
            return Response({"message": "Classroom is required."}, status=status.HTTP_400_BAD_REQUEST)

        common = request.data.get("common", [])
        errors = []
        for idx, item in enumerate(common):
            entry = {
                "start_time": f"{item['start']['hour']}:{item['start']['minute']}:00",
                "end_time": f"{item['end']['hour']}:{item['end']['minute']}:00",
                "subject": item.get("subject"),
                "classroom": classroom_id,
            }
            serializer = self.get_serializer(data=entry)
            if serializer.is_valid():
                serializer.save()
            else:
                errors.append({"row": idx, "errors": serializer.errors})

        if errors:
            return Response(errors, status=status.HTTP_200_OK)
        return Response({"message": "Common Time Added Successfully"}, status=status.HTTP_201_CREATED)


# ── Syllabus ───────────────────────────────────────────────────────────────────


class SyllabusView(SchoolContextMixin, viewsets.ModelViewSet):
    serializer_class = serializers.SyllabusSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]

    def get_queryset(self):
        from api.models import SyllabusModel

        school = self.get_school()
        session = self.get_active_session(school)
        classroom_id = self.request.query_params.get("classroom")

        if classroom_id:
            return SyllabusModel.objects.filter(classroom_id=classroom_id, school=school, session=session)

        # For teachers: show syllabi for their classes
        try:
            teacher = StaffModel.objects.get(user=self.request.user)
            own = ClassroomModel.objects.filter(
                Q(class_teacher=teacher) | Q(sub_class_teacher=teacher), session=session
            )
            teaches_ids = Subject.objects.filter(teacher=teacher, session=session).values_list("classroom", flat=True)
            all_classrooms = (own | ClassroomModel.objects.filter(id__in=teaches_ids, session=session)).distinct()
            return SyllabusModel.objects.filter(classroom__in=all_classrooms, school=school, session=session)
        except StaffModel.DoesNotExist:
            return SyllabusModel.objects.filter(school=school, session=session)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.SyllabusListSerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        # Validate that the subject exists in the classroom
        school = self.get_school()
        subject_id = request.data.get("subject")
        classroom_id = request.data.get("classroom")
        if not Subject.objects.filter(id=subject_id, classroom_id=classroom_id, school=school).exists():
            return Response(
                {"message": "Subject does not exist in this classroom."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Syllabus Added Successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )
