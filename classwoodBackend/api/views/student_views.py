from rest_framework import generics,status,viewsets,mixins
from rest_framework.response import Response
from .. import models
from ..permissions import AdminPermission,StudentLevelPermission,IsTokenValid,ReadOnlyStaffPermission,ReadOnlyStudentPermission,StaffLevelPermission
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema,OpenApiParameter,OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .. import serializers
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..utils import generate_staff_user
import csv
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from django.http import QueryDict
import datetime

class StudentSingleView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.StudentListSerializer
    permission_classes = [IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid]

    def get_object(self):
        student = models.StudentModel.objects.get(user=self.request.user)
        student.user.password = None
        return student

    def patch(self, request):
        data = request.data.copy()
        student = self.get_object()
        school = student.school
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
        if data.get('user') is not None:
            return Response(data={"message":"Account credentials cannot be changed. Contact Administrator"},status=status.HTTP_200_OK)
        if data.get('school') is not None:
            return Response(data={"message":"School cannot be changed. Contact Administrator"},status=status.HTTP_200_OK)
        serializer = self.serializer_class(student,data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)

class StudentSubjectView(generics.ListAPIView):
    serializer_class = serializers.SubjectListSerializer
    permission_classes = [IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid]

    def get_queryset(self):
        school = (models.StudentModel.objects.get(user=self.request.user)).school
        # session = self.request.GET.get('session',None)
        # if session is None:
        #     session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        student = models.StudentModel.objects.get(user=self.request.user,session=session)
        return models.Subject.objects.filter(Q(classroom=student.classroom) & Q(school = student.school),session=session)

class StudentSyllabusView(generics.ListAPIView):
    serializer_class = serializers.SyllabusListSerializer
    permission_classes = [IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid]

    def get_queryset(self):
        school = (models.StudentModel.objects.get(user=self.request.user)).school
        # session = self.request.GET.get('session',None)
        # if session is None:
        #     session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        student = models.StudentModel.objects.get(user=self.request.user)
        return models.SyllabusModel.objects.filter(Q(subject__classroom=student.classroom) & Q(subject__school = student.school))

class StudentResultView(generics.ListAPIView):
    serializer_class = serializers.ResultListSerializer
    permission_classes = [IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid]

    def get_queryset(self):
        school = (models.StudentModel.objects.get(user=self.request.user)).school
        exam = self.request.GET.get('exam',None)
        # session = self.request.GET.get('session',None)
        # if session is None:
        #     session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        student = models.StudentModel.objects.get(user=self.request.user)
        if exam is not None:
            return models.ResultModel.objects.filter(student=student,exam=exam)
        return models.ResultModel.objects.filter(student=student)
    
class ThoughtOfDayView(generics.RetrieveAPIView):
    serializer_class = serializers.ThoughtDaySerializer
    permission_classes = [IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid]

    def get_object(self):
        date = self.request.GET.get('date',datetime.datetime.now().date())
        return models.ThoughtDayModel.objects.get(date=date)
    
class FeeStudentView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated & (StudentLevelPermission | AdminPermission | StaffLevelPermission) & IsTokenValid]
    
    def get(self, request):
        student = models.StudentModel.objects.get(user=self.request.user)
        classroom = student.classroom
        fees = models.FeesDetails.objects.filter(for_class=classroom)
        data = {}
        data['fees'] = fees
        total_amt = 0
        for fee in fees:
            total_amt = total_amt + fees.amount
        data['total_amt'] = total_amt
        discount = student.waiver_percent
        data['amt_to_be_paid'] = total_amt - (total_amt * discount)
        return Response(data=data)
    

