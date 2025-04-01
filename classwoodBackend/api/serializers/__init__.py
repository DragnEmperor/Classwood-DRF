# Re-export all serializers for convenient imports.

from api.serializers.academics import (
    CommonTimeListSerializer,
    CommonTimeSerializer,
    ExamCreateSerializer,
    ExamListSerializer,
    ResultListSerializer,
    ResultSerializer,
    SyllabusListSerializer,
    SyllabusSerializer,
    TimeTableListSerializer,
    TimeTableSerializer,
)
from api.serializers.accounts import (
    AccountSerializer,
    ForgotPasswordSerializer,
    VerifyOTPSerializer,
)
from api.serializers.attendance import (
    StaffAttendanceListSerializer,
    StaffAttendanceSerializer,
    StudentAttendanceListSerializer,
    StudentAttendanceSerializer,
)
from api.serializers.classroom import (
    ClassroomCreateSerializer,
    ClassroomListSerializer,
    SubjectCreateSerializer,
    SubjectListSerializer,
)
from api.serializers.communications import (
    EventListSerializer,
    EventSerializer,
    NoticeCreateSerializer,
    NoticeListSerializer,
    ThoughtDaySerializer,
)
from api.serializers.fees import (
    FeesDetailsSerializer,
    FeesListSerializer,
    PaymentCreateSerializer,
    PaymentInfoSerializer,
)
from api.serializers.school import (
    SchoolProfileSerializer,
    SchoolSignUpSerializer,
    SessionSerializer,
)
from api.serializers.staff import StaffCreateSerializer, StaffListSerializer
from api.serializers.student import StudentCreateSerializer, StudentListSerializer

__all__ = [
    # Accounts
    "AccountSerializer",
    "ForgotPasswordSerializer",
    "VerifyOTPSerializer",
    # School
    "SchoolSignUpSerializer",
    "SchoolProfileSerializer",
    "SessionSerializer",
    # Staff
    "StaffCreateSerializer",
    "StaffListSerializer",
    # Student
    "StudentCreateSerializer",
    "StudentListSerializer",
    # Classroom
    "ClassroomCreateSerializer",
    "ClassroomListSerializer",
    "SubjectCreateSerializer",
    "SubjectListSerializer",
    # Attendance
    "StudentAttendanceSerializer",
    "StudentAttendanceListSerializer",
    "StaffAttendanceSerializer",
    "StaffAttendanceListSerializer",
    # Academics
    "ExamCreateSerializer",
    "ExamListSerializer",
    "ResultSerializer",
    "ResultListSerializer",
    "SyllabusSerializer",
    "SyllabusListSerializer",
    "TimeTableSerializer",
    "TimeTableListSerializer",
    "CommonTimeSerializer",
    "CommonTimeListSerializer",
    # Communications
    "NoticeCreateSerializer",
    "NoticeListSerializer",
    "EventSerializer",
    "EventListSerializer",
    "ThoughtDaySerializer",
    # Fees
    "FeesDetailsSerializer",
    "FeesListSerializer",
    "PaymentCreateSerializer",
    "PaymentInfoSerializer",
]
