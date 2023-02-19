from django.urls import path,include
from .views.school_views import SchoolSignUpView,StaffView,ClassroomSchoolView,SchoolProfileView,NoticeView
from .views.staff_views import StaffSingleView,ClassroomStaffView,SubjectCreateView,StudentCreateView,AttendanceView
from .views.general_views import LoginView,LogoutView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register('staff', StaffView)
router.register('classroom', ClassroomSchoolView)
router.register('notice', NoticeView)

router2 = DefaultRouter()
router2.register('classroom', ClassroomStaffView)
router2.register('subject', SubjectCreateView)
router2.register('student', StudentCreateView)
router2.register('attendance', AttendanceView)

urlpatterns = [
    path("signup/",SchoolSignUpView.as_view(),name="school_signup"),
    path('login/', LoginView.as_view(), name='token_obtain_pair'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    path("account/",SchoolProfileView.as_view(),name="school_profile"),
    # path("staff/create",StaffCreateView.as_view(),name="staff_signup"),
    path("list/",include(router.urls),name="viewset_views_lists"),
    path("staff/me",StaffSingleView.as_view(),name="staff_profile"),
    path("staff/",include(router2.urls),name="staff_classroom_list"),
]
