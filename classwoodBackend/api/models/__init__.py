# Re-export all models so `from api.models import X` and migration references work.

from api.models.academics import (
    CommonTimeModel,
    ExamModel,
    ResultModel,
    SyllabusModel,
    TimeTableModel,
)
from api.models.accounts import Accounts, BlackListedToken, OTPModel
from api.models.attendance import (
    StaffAttendance,
    StaffYearAttendance,
    StudentAttendance,
    StudentYearAttendance,
)
from api.models.classroom import ClassroomModel, Subject, subject_profile_upload
from api.models.communications import (
    Attachment,
    EventModel,
    Notice,
    ThoughtDayModel,
    notice_attach_upload,
)
from api.models.fees import FeesDetails, PaymentInfo
from api.models.school import SchoolModel, SessionModel, school_logo_upload
from api.models.staff import StaffModel, staff_profile_upload
from api.models.student import StudentModel, student_profile_upload

__all__ = [
    # Accounts
    "Accounts",
    "BlackListedToken",
    "OTPModel",
    # School
    "SchoolModel",
    "SessionModel",
    "school_logo_upload",
    # People
    "StaffModel",
    "staff_profile_upload",
    "StudentModel",
    "student_profile_upload",
    # Classroom
    "ClassroomModel",
    "Subject",
    "subject_profile_upload",
    # Attendance
    "StudentAttendance",
    "StaffAttendance",
    "StudentYearAttendance",
    "StaffYearAttendance",
    # Academics
    "ExamModel",
    "ResultModel",
    "SyllabusModel",
    "TimeTableModel",
    "CommonTimeModel",
    # Communications
    "Attachment",
    "Notice",
    "EventModel",
    "ThoughtDayModel",
    "notice_attach_upload",
    # Fees
    "FeesDetails",
    "PaymentInfo",
]
