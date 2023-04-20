from django.shortcuts import get_object_or_404
from rest_framework import generics,status,viewsets
from .. import serializers
from rest_framework.response import Response
from rest_framework.request import Request
from ..permissions import AdminPermission,IsTokenValid,ReadOnlyStaffPermission,ReadOnlyStudentPermission
from rest_framework.permissions import IsAuthenticated
from .. import models
import csv,pyotp
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password,check_password
from django.core.mail import send_mail
from django.http import Http404
from django.utils import timezone
import datetime

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

    def post(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
          user = get_object_or_404(User,email=serializer.validated_data['email'])
        except Http404:
            return Response(data={"message":"No User associated with this email found"},status=status.HTTP_200_OK)
        try:
           school_user = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
            return Response(data={"message":"No School Account associated with this email found"},status=status.HTTP_200_OK)
        otp_base32 = pyotp.random_base32()
        otp = pyotp.TOTP(otp_base32,digits=6)
        final_otp = otp.now()
        expiration_time = timezone.now() + timezone.timedelta(minutes=5)
        hashed_otp = make_password(final_otp)
        models.OTPModel.objects.create(email=user.email,hashed_otp=hashed_otp,expiration_time=expiration_time)
        message=f'The request to change your password has been received.\n To continue, use the folowing OTP :\n {final_otp}.\n\n This OTP is valid only for 5 minutes.'
        send_mail('Forgot Password ClassWood',message,settings.EMAIL_HOST_USER,[user.email],fail_silently=False)
        return Response({'message':'An OTP to reset your password has been sent to your email.\nNote : It is valid only for 5 minutes.'},status=status.HTTP_200_OK)

class VerifyOTPView(generics.GenericAPIView):
    serializer_class = serializers.VerifyOTPSerializer

    def post(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['password']
        otp_obj = models.OTPModel.objects.filter(email=email).last()

        if otp_obj and check_password(otp, otp_obj.hashed_otp) and otp_obj.email==email and otp_obj.expiration_time > timezone.now():
           otp_obj.delete()
           user = get_object_or_404(User, email=email)
           user.password = make_password(new_password)
           user.save()

            # send the new password to the user's email
           message = f'The password for your ClassWood account has been changed.\n Your new password is {new_password}.\n\nIf not done by you then contact admin.'
           send_mail('New Password set',message,settings.EMAIL_HOST_USER,[user.email],fail_silently=False)

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
        school= models.SchoolModel.objects.get(user = self.request.user)
        session = self.request.GET.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        staff = models.StaffModel.objects.filter(school=school,session=session)
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
            session = request.data.get('session',None)
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
               doj = row.get('Date of Joining',None)
               try:
                   doj = datetime.datetime.strptime(doj,'%Y-%m-%d')
               except ValueError:
                   doj = datetime.datetime.strptime(doj,'%d-%m-%Y')
               doj = doj.strftime('%Y-%m-%d')
               data['date_of_joining'] = doj
               school = models.SchoolModel.objects.get(user=request.user)
               if session is None:
                   session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
                   data['session'] = session.id
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
           session = data.get('session',None)
           if session is None:
                session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
                data['session'] = session.id
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
        school= models.SchoolModel.objects.get(user = self.request.user)
        session = self.request.GET.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        classrooms = models.ClassroomModel.objects.filter(school= school,session=session)
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
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
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
    permission_classes = [IsAuthenticated & (ReadOnlyStaffPermission | ReadOnlyStudentPermission |AdminPermission) & IsTokenValid]
    queryset = models.Notice.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.NoticeListSerializer
        return self.serializer_class

    def get_queryset(self):
        user = self.request.user
        session = self.request.GET.get('session',None)
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if session is None:
            session = session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        return models.Notice.objects.filter(school=school,session=session)


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
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Notice Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)

class EventView(viewsets.ModelViewSet):
    serializer_class = serializers.EventSerializer
    queryset = models.EventModel.objects.all()
    permission_classes = [IsAuthenticated & (ReadOnlyStaffPermission | ReadOnlyStudentPermission |AdminPermission) & IsTokenValid]

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.EventListSerializer
        return self.serializer_class

    def get_queryset(self):
        user = self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        except models.StaffModel.DoesNotExist:
          school = (models.StudentModel.objects.get(user=user)).school
        return models.EventModel.objects.filter(school=school)

    def create(self, request):
        data = request.data.copy()
        user = request.user
        school = models.SchoolModel.objects.get(user=user)
        data['school'] = school
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Event Created Successfully", "data": serializer.data}
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
        attendance = models.StaffAttendance.objects.filter(school=school)
        return attendance

    def create(self, request):
        data = request.data.copy()
        user = request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          return Response(data={"message":"You are not a school admin"},status=status.HTTP_200_OK)
        data['school'] = school
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Staff Attendance Marked Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)

class SessionView(viewsets.ModelViewSet):
    serializer_class = serializers.SessionSerializer
    queryset = models.SessionModel.objects.all()
    permission_classes = [IsAuthenticated & (AdminPermission | ReadOnlyStaffPermission) & IsTokenValid]

    def get_queryset(self):
        user = self.request.user
        school = models.SchoolModel.objects.get(user=user)
        active_sessions = models.SessionModel.objects.filter(school_id=school,is_active=True).order_by('-start_date').all()
        for session in active_sessions:
            session.deactivate_if_expired
        return models.SessionModel.objects.filter(school=school)

    def create(self, request):
        data = request.data.copy()
        user = request.user
        start_date = data.get('start_date',datetime.datetime.now().date())
        try:
          school = models.SchoolModel.objects.get(user=user)
          sessions = models.SessionModel.objects.filter(school=school).order_by('-start_date').all()
          if(len(sessions) >= 2):
              session = sessions[1]
              if session and session.is_active:
                 return Response({'message': 'More than Two active sessions not allowed.'})
        except models.SchoolModel.DoesNotExist:
          return Response(data={"message":"You are not a school admin"},status=status.HTTP_200_OK)
        data['school'] = school
        data['start_date'] = start_date
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Session Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)

    def partial_update(self, request):
        user = request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
          session = models.SessionModel.objects.filter(school=school).order_by('-start_date').first()
          if not session or not session.is_active:
            return Response({'message': 'No Active session found'})
          serializer = self.get_serializer(session, data=request.data, partial=True)
          serializer.is_active = False
          session.end_date = datetime.now().date()
          session.save()
          return Response(serializers.SessionSerializer(session).data,status=status.HTTP_200_OK)
        #   if(serializer.is_valid()):
        #     self.perform_update(serializer)
        #     return Response(serializer.data,status=status.HTTP_200_OK)
        #   return Response(serializer.errors,status=status.HTTP_200_OK)
        except models.SchoolModel.DoesNotExist:
          return Response(data={"message":"You are not a school admin"},status=status.HTTP_200_OK)

class ThoughtsView(viewsets.ModelViewSet):
    serializer_class = serializers.ThoughtDaySerializer
    queryset = models.ThoughtDayModel.objects.all()
    permission_classes = [IsAuthenticated & (AdminPermission | ReadOnlyStaffPermission | ReadOnlyStudentPermission ) & IsTokenValid]

    def get_queryset(self):
        user = self.request.user
        school = models.SchoolModel.objects.get(user=user)
        session = self.request.GET.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        return models.ThoughtDayModel.objects.filter(school=school,session=session)

    def create(self, request):
        data = request.data.copy()
        user = request.user
        school = models.SchoolModel.objects.get(user=user)
        data['school'] = school
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Thought Day Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)

class FeesDetailsView(viewsets.ModelViewSet):
    queryset = models.FeesDetails.objects.all()
    permission_classes = [IsAuthenticated & (AdminPermission | ReadOnlyStaffPermission | ReadOnlyStudentPermission) & IsTokenValid]
    serializer_class = serializers.FeesDetailsSerializer

    def get_queryset(self):
        user=self.request.user
        school = models.SchoolModel.objects.get(user=user)
        classroom = self.request.GET.get('classroom',None)
        session = self.request.GET.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        if classroom is None:
            return models.FeesDetails.objects.filter(school=school,session=session)
        return models.FeesDetails.objects.filter(school=school,session=session,for_class=classroom)

    def create(self, request):
        data = request.data.copy()
        errors=[]
        user = request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          return Response(data={"message":"You are not a school admin"},status=status.HTTP_200_OK)
        data['school'] = school
        session = data.get('session',None)
        student_data = data.pop('student_data')
        for student in student_data:
            stud_user = student.get('user')
            get_student = models.StudentModel.objects.get(user=stud_user.get('id'))
            concession =  student.get('concession')
            get_student.waiver_type = concession.get('title')
            get_student.waiver_percent = (int(concession.get('value')))/100
            get_student.save()
        fee_data = data.pop('fee_data')
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
        for row_num,fee in enumerate(fee_data,1):
            data['amount'] = fee.get('fees')
            data['fee_type'] = fee.get('title')
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
                return Response(data={"message":"Fees Added Successfully"},status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)










