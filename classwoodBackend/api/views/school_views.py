from django.shortcuts import render,get_object_or_404
from rest_framework import generics,status,viewsets,serializers
from .. import serializers
from rest_framework.response import Response
from rest_framework.request import Request
from ..permissions import AdminPermission,StaffLevelPermission,IsTokenValid,ReadOnlyStaffPermission
from rest_framework.permissions import IsAuthenticated
from .. import models
import json,csv,base64,pyotp
from django.core.serializers import serialize
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
 
User = get_user_model()

class SchoolSignUpView(generics.CreateAPIView):
    serializer_class = serializers.SchoolSignUpSerializer
    permission_classes = []
    def post(self, request: Request):  
        data = request.data.copy()
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.save()
            response = {"message": "School User Created Successfully", "data": serializer.data}
            return Response(data=response, status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_200_OK)
    
class ForgotPasswordView(generics.GenericAPIView):
    serializer_class = serializers.ForgotPasswordSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]
    
    def post(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User,email=serializer.validated_data['email'])
        try:
           school_user = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
            return Response(data={"message":"No School Account associated with this email found"},status=status.HTTP_200_OK)
        otp_base32 = pyotp.random_base32()
        otp = pyotp.TOTP(otp_base32,digits=6)
        message=f'The request to change your password has been received.\n To continue, use the folowing OTP :\n {otp.now()}.'
        send_mail('Forgot Password ClassWood',message,settings.EMAIL_HOST_USER,[user.email],fail_silently=False)
        request.session['otp'] = otp.now()
        request.session['email'] = user.email
        return Response({'message':'An OTP to reset your password has been sent to your email'},status=status.HTTP_200_OK)
    
class VerifyOTPView(generics.GenericAPIView):
    serializer_class = serializers.VerifyOTPSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]
    
    def post(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['password']
        
        if otp == request.session.get('otp') and email == request.session.get('email'):
           user = get_object_or_404(User, email=email)
           user.password = make_password(new_password)
           user.save()
            
            # send the new password to the user's email
           message = f'The password for your ClassWood account has been changed.\n Your new password is {new_password}.\n\nIf not done by you then contact admin.'
           send_mail('New Password set',message,settings.EMAIL_HOST_USER,[user.email],fail_silently=False)
           del request.session['otp']
           del request.session['email']
           
           return Response({'message':'Password Changed Successfully'},status=status.HTTP_200_OK)
        return Response({'message':'Invalid OTP! Please Try Again'},status=status.HTTP_200_OK)
    
class SchoolProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.SchoolProfileSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]
    
    def get_object(self):
        school = models.SchoolModel.objects.get(user=self.request.user)
        school.user.password = None
        return school
    
    def patch(self,request):
        data = request.data.copy()
        school = self.get_object()
        serializer = self.serializer_class(school,data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)
    
class StaffView(viewsets.ModelViewSet):
    serializer_class = serializers.StaffCreateSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]
    queryset = models.StaffModel.objects.all()

     
    def get_queryset(self):
        user = self.request.user
        staff = models.StaffModel.objects.filter(school= models.SchoolModel.objects.get(user=user))
        for items in staff:
            items.user.password = None
        return staff
    
    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.StaffListSerializer
        return self.serializer_class
    
    def destroy(self, request, *args, **kwargs):
        id = self.kwargs['pk']
        staff = get_object_or_404(models.Accounts, id=id)
        staff.delete()
        return Response(status=204)
    
    def create(self,request):
        csv_file = request.FILES.get('csv_file',None)
        data = {}
        errors=[]
        if csv_file:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            for row_num, row in enumerate(reader, 1):
               if not all(row.values()):
                    break
               data['first_name'] = row.get('First Name',None)
               data['last_name'] = row.get('Last Name',None)
               data['date_of_birth'] = row.get('DOB',None)
               data['gender'] = '1' if row.get('Gender',None)=='M' else '2' if row.get('Gender',None)=='F' else '3'
               data['contact_email'] = row.get('Email',None)
               data['mobile_number'] = row.get('Mobile',None)
               data['address'] = row.get('Address',None)
               data['account_no'] = row.get('Account_no',None)
               data['date_of_joining'] = row.get('Date of Joining',None)
               school = models.SchoolModel.objects.get(user=request.user)
               data['school'] = school
               serializer = self.serializer_class(data=data)
               if serializer.is_valid():
                   serializer.save()
                   pass
               else:
                   errors.append({
                        'row': row_num,
                        'errors': serializer.errors
                    })
            if errors:  
                return Response(data=errors,status=status.HTTP_200_OK)
            else:
                return Response(data={"message":"Staff Added from CSV Successfully"},status=status.HTTP_201_CREATED)
        else:
           data = request.data.copy()
           school = models.SchoolModel.objects.get(user=request.user)
           data['school'] = school
           serializer = self.serializer_class(data=data)
           if serializer.is_valid():
             serializer.save()
             response = {"message": "Staff Created Successfully", "data": serializer.data}
             return Response(data=response,status=status.HTTP_201_CREATED)
           return Response(data=serializer.errors,status=status.HTTP_200_OK)
       
    
class ClassroomSchoolView(viewsets.ModelViewSet):
    serializer_class = serializers.ClassroomCreateSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]
    queryset = models.ClassroomModel.objects.all()
     
    def get_queryset(self):
        user = self.request.user
        classrooms = models.ClassroomModel.objects.filter(school= models.SchoolModel.objects.get(user=user))
        return classrooms
    
    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.ClassroomListSerializer
        return serializers.ClassroomCreateSerializer
    
    def destroy(self, request, *args, **kwargs):
        classroom = models.ClassroomModel.objects.get(id=self.kwargs['pk'])
        models.StaffModel.objects.filter(user=classroom.class_teacher).update(is_class_teacher=False)
        classroom.delete()
        return Response(status=204)
    
    def create(self,request):
        data = request.data.copy()
        user = request.user
        school = models.SchoolModel.objects.get(user=user)
        data['school'] = school
        class_teacher_account  = models.Accounts.objects.get(id=data.get('class_teacher'))
        class_teacher = models.StaffModel.objects.get(user=class_teacher_account)
        if class_teacher.is_class_teacher == True:
            return Response(data={"message":"Class Teacher Already Assigned"},status=status.HTTP_200_OK)
        data['class_teacher'] = class_teacher
        if data.get('sub_class_teacher',None) is not None:
          sub_teacher_account  = models.Accounts.objects.get(id=data.get('sub_class_teacher'))
          data['sub_class_teacher'] = models.StaffModel.objects.get(user=sub_teacher_account)
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            models.StaffModel.objects.filter(user=class_teacher_account).update(is_class_teacher=True)
            response = {"message": "Classroom Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        
        return Response(data=serializer.errors,status=status.HTTP_200_OK)
    
class NoticeView(viewsets.ModelViewSet):
    serializer_class = serializers.NoticeCreateSerializer
    permission_classes = [IsAuthenticated & (ReadOnlyStaffPermission | AdminPermission) & IsTokenValid]
    queryset = models.Notice.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.NoticeListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        user = self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        return models.Notice.objects.filter(school=school)
    
    
    def get_object(self):
        notice = super().get_object() 
        studentuser = None
        try:
         studentuser = models.StudentModel.objects.get(user = self.request.user)
        except models.StudentModel.DoesNotExist:
            try:
               staffuser = models.StaffModel.objects.get(user = self.request.user)
            except models.StaffModel.DoesNotExist:
               return notice
        if studentuser is not None:
            notice.read_by_students.add(studentuser)
        else:
            notice.read_by_staff.add(staffuser)
        notice.save()
        return notice
    
    def create(self, request):
        data = request.data.copy()
        user = request.user
        school = models.SchoolModel.objects.get(user=user)
        data['school'] = school
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Notice Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)
    
class StaffAttendanceView(viewsets.ModelViewSet):
    serializer_class = serializers.StaffAttendanceSerializer
    queryset = models.StaffAttendance.objects.all()
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]
    
    def get_serializer_class(self):
        if self.action=='list':
            return serializers.StaffAttendanceListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        user=self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
          attendance = models.StaffAttendance.objects.filter(classroom=get_classroom,school=school)
        return attendance
    
    def create(self, request):
        data = request.data.copy()
        user = request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          return Response(data={"message":"You are not a school admin"},status=status.HTTP_200_OK)
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Staff Attendance Marked Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)
    
    
    
        
    
        
    
    
    
    
