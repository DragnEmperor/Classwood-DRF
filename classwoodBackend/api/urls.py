from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from api.views import general_views, school_views, staff_views, student_views

# School-admin router
school_router = DefaultRouter()
school_router.register("staff", school_views.StaffView, basename="staff")
school_router.register("classroom", school_views.ClassroomSchoolView, basename="classroom")
school_router.register("notice", school_views.NoticeView, basename="notice")
school_router.register("staffAttendance", school_views.StaffAttendanceView, basename="staffattendance")
school_router.register("event", school_views.EventView, basename="event")
school_router.register("session", school_views.SessionView, basename="session")
school_router.register("thoughtDay", school_views.ThoughtsView, basename="thoughtday")
school_router.register("fees", school_views.FeesDetailsView, basename="fees")

# Staff router
staff_router = DefaultRouter()
staff_router.register("classroom", staff_views.ClassroomStaffView, basename="staff-classroom")
staff_router.register("subject", staff_views.SubjectCreateView, basename="subject")
staff_router.register("student", staff_views.StudentListCreateView, basename="student")
staff_router.register("studentAttendance", staff_views.StudentAttendanceView, basename="studentattendance")
staff_router.register("exam", staff_views.ExamView, basename="exam")
staff_router.register("result", staff_views.ResultView, basename="result")
staff_router.register("syllabus", staff_views.SyllabusView, basename="syllabus")
staff_router.register("timeTable", staff_views.TimeTableView, basename="timetable")
staff_router.register("commontime", staff_views.CommonTimeView, basename="commontime")

urlpatterns = [
    # Auth
    path("signup/", school_views.SchoolSignUpView.as_view(), name="school_signup"),
    path("login/", general_views.LoginView.as_view(), name="token_obtain_pair"),
    path("logout/", general_views.LogoutView.as_view(), name="logout"),
    path("refresh-token/", TokenRefreshView.as_view(), name="token_refresh"),
    path("forgot-password/", school_views.ForgotPasswordView.as_view(), name="forgot_password"),
    path("verify-otp/", school_views.VerifyOTPView.as_view(), name="verify_otp"),
    # School admin
    path("account/", school_views.SchoolProfileView.as_view(), name="school_profile"),
    path("list/", include(school_router.urls)),
    # Fees
    path("list/payments/", school_views.PaymentHistoryView.as_view(), name="payment_history"),
    path("list/student/", school_views.StudentListView.as_view(), name="all_students"),
    # Staff
    path("staff/exam/mark/<uuid:pk>", staff_views.ExamMarkView.as_view(), name="mark_exam"),
    path("staff/", include(staff_router.urls)),
    path("staff/me/", staff_views.StaffSingleView.as_view(), name="staff_profile"),
    # Student
    path("student/me/", student_views.StudentSingleView.as_view(), name="student_profile"),
    path("student/subjects/", student_views.StudentSubjectView.as_view(), name="student_subjects"),
    path("student/syllabus/", student_views.StudentSyllabusView.as_view(), name="student_syllabus"),
    path("student/result/", student_views.StudentResultView.as_view(), name="student_result"),
    path("student/thoughtDay/", student_views.ThoughtOfDayView.as_view(), name="thought_day"),
    path("student/fees/", student_views.FeeStudentView.as_view(), name="single_student_fees"),
]
