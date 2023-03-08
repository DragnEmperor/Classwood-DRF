from django.urls import path,include
from .views import staff_views,school_views
from .views.general_views import LoginView,LogoutView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register('staff', school_views.StaffView)
router.register('classroom', school_views.ClassroomSchoolView)
router.register('notice', school_views.NoticeView)

router2 = DefaultRouter()
router2.register('classroom', staff_views.ClassroomStaffView)
router2.register('subject', staff_views.SubjectCreateView)
router2.register('student', staff_views.StudentCreateView)
router2.register('attendance', staff_views.AttendanceView)
router2.register('exam', staff_views.ExamView)
router2.register('result', staff_views.ResultView)

urlpatterns = [
    path("signup/",school_views.SchoolSignUpView.as_view(),name="school_signup"),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path("account/",school_views.SchoolProfileView.as_view(),name="school_profile"),
    # path("staff/create",StaffCreateView.as_view(),name="staff_signup"),
    path("list/",include(router.urls),name="viewset_views_lists"),
    path("staff/me",staff_views.StaffSingleView.as_view(),name="staff_profile"),
    path("staff/",include(router2.urls),name="staff_classroom_list"),
]
