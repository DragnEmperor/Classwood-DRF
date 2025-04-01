from django.contrib.auth import authenticate, get_user_model
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from api.models import BlackListedToken, SchoolModel, SessionModel, StaffModel, StudentModel
from api.permissions import IsTokenValid
from api.utils import create_jwt_pair

User = get_user_model()


def get_user_school_and_type(user):
    school = SchoolModel.objects.filter(user=user).first()
    if school:
        return school, "School"

    staff = StaffModel.objects.select_related("school").filter(user=user).first()
    if staff:
        return staff.school, "Staff"

    student = StudentModel.objects.select_related("school").filter(user=user).first()
    if student:
        return student.school, "Student"

    return None, None


class LoginView(TokenObtainPairView):
    permission_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)

        if user is None:
            return Response({"message": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = create_jwt_pair(user)

        school, user_type = get_user_school_and_type(user)
        if school is None:
            return Response({"message": "No school account found for this user"}, status=status.HTTP_403_FORBIDDEN)

        if not SessionModel.objects.filter(school=school, is_active=True).exists():
            return Response(
                {"message": "No active session found for the user's school"}, status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {"message": "Login Successful", "tokens": tokens, "user_type": user_type},
            status=status.HTTP_200_OK,
        )


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated & IsTokenValid]

    def post(self, request):
        BlackListedToken.objects.create(token=request.auth, user=request.user)
        return Response({"status": "OK, goodbye"}, status=status.HTTP_200_OK)
