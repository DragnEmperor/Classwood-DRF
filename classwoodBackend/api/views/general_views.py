from django.contrib.auth import get_user_model,authenticate
from ..models import SchoolModel,BlackListedToken,StaffModel,StudentModel
# from ..serializers import AuthTokenSerializer
from ..function import create_jwt_pair
from ..permissions import IsTokenValid
from rest_framework import generics,status,views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from paytmchecksum import PaytmChecksum
import requests

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
            staff = StaffModel.objects.filter(user=user).exists()
            user_type = "Student"
            if staff:
              user_type = "Staff"
            schoolAdmin = SchoolModel.objects.filter(user=user).exists()
            if schoolAdmin:
              user_type = "School"
            response = {"message": "Login Successfull", "tokens": tokens,"user_type":user_type}
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
    

class PaytmPaymentAPIView(APIView):
    @csrf_exempt
    def post(self, request):
        amount = request.data['amount'] # amount to be paid by user
        email = request.data['email'] # email of the user
        mobile = request.data['mobile'] # mobile number of the user
        order_id = request.data['order_id'] # unique order id
        callback_url = "http://127.0.0.1:8000/paytm-callback/" # callback URL for paytm to redirect to after payment
        paytm_params = {
            "MID": "your-merchant-id",
            "ORDER_ID": order_id,
            "TXN_AMOUNT": str(amount),
            "CUST_ID": email,
            "MOBILE_NO": mobile,
            "EMAIL": email,
            "CHANNEL_ID": "WEB",
            "WEBSITE": "your-website",
            "INDUSTRY_TYPE_ID": "Retail",
            "CALLBACK_URL": callback_url,
        }
        paytm_checksum = PaytmChecksum.generateSignature(paytm_params, "your-merchant-key")
        paytm_params["CHECKSUMHASH"] = paytm_checksum
        paytm_url = "https://securegw-stage.paytm.in/theia/processTransaction"
        response = requests.post(paytm_url, json=paytm_params)
        return Response(response.json())
      
      
class PaytmCallbackAPIView(APIView):
    @csrf_exempt
    def post(self, request):
        paytm_params = dict(request.POST)
        paytm_checksum = paytm_params.pop('CHECKSUMHASH')[0]
        is_valid_checksum = PaytmChecksum.verifySignature(paytm_params, "your-merchant-key", paytm_checksum)
        if is_valid_checksum:
            # Payment successful, update your database and return success response
            return Response({"message": "Payment successful"})
        else:
            # Payment failed, return error response
            return Response({"message": "Payment failed"})

        
    
    

