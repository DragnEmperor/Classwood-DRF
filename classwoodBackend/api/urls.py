from django.urls import path,include
from .views.school_views import SchoolSignUpView,StaffView,ClassroomSchoolView
from .views.staff_views import StaffSingleView,ClassroomStaffView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('staff', StaffView)
router.register('classroom', ClassroomSchoolView)

router2 = DefaultRouter()
router2.register('classroom', ClassroomStaffView)

urlpatterns = [
    path("signup/",SchoolSignUpView.as_view(),name="school_signup"),
    # path("staff/create",StaffCreateView.as_view(),name="staff_signup"),
    path("list/",include(router.urls),name="viewset_views_lists"),
    path("staff/me",StaffSingleView.as_view(),name="staff_profile"),
    path("staff/",include(router2.urls),name="staff_classroom_list"),
]
