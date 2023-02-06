from django.contrib.auth import get_user_model,authenticate
from ..models import SchoolModel,BlackListedToken
# from ..serializers import AuthTokenSerializer
from ..function import create_jwt_pair
from ..permissions import IsTokenValid
from rest_framework import generics,status,views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()


class LoginView(TokenObtainPairView):
    # serializer_class = AuthTokenSerializer
    permission_classes = []
    
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email,password=password)
        if user is not None:
            tokens = create_jwt_pair(user)
            response = {"message": "Login Successfull", "tokens": tokens}
            return Response(data=response,status=status.HTTP_200_OK)
        else:
            return Response(data={"message": "Invalid email or password"})
    
    def get(self,request):
        content = {"user":str(request.user), "auth":str(request.auth)}
        return Response(data=content,status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated & IsTokenValid]

    def post(self, request, *args, **kwargs):
        # if self.request.data.get('all'):
        #     token: OutstandingToken
        #     for token in OutstandingToken.objects.filter(user=request.user):
        #         _, _ = BlacklistedToken.objects.get_or_create(token=token)
        #     return Response({"status": "OK, goodbye, all refresh tokens blacklisted"})
        refresh_token = self.request.auth
        blacklistToken = BlackListedToken.objects.create(token=refresh_token,user=self.request.user)
        return Response({"status": "OK, goodbye"})
    
    

