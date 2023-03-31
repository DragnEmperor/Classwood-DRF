from rest_framework import generics,status,viewsets,mixins
from rest_framework.response import Response
from .. import models
from ..permissions import AdminPermission,StudentLevelPermission,IsTokenValid,ReadOnlyStaffPermission,ReadOnlyStudentPermission
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

class StudentSingleView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.StudentListSerializer
    permission_classes = [IsAuthenticated & StudentLevelPermission & ~AdminPermission & IsTokenValid]
    
    def get_object(self):
        student = models.StudentModel.objects.get(user=self.request.user)
        student.user.password = None
        return student
    
    def patch(self, request):
        data = request.data.copy()
        student = self.get_object()
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
    permission_classes = [IsAuthenticated & StudentLevelPermission & ~AdminPermission & IsTokenValid]
    
    def get_queryset(self):
        student = models.StudentModel.objects.get(user=self.request.user)
        return models.Subject.objects.filter(Q(classroom=student.classroom) & Q(school = student.school))
    
class StudentSyllabusView(generics.ListAPIView):
    serializer_class = serializers.SyllabusListSerializer
    permission_classes = [IsAuthenticated & StudentLevelPermission & ~AdminPermission & IsTokenValid]
    
    def get_queryset(self):
        student = models.StudentModel.objects.get(user=self.request.user)
        return models.SyllabusModel.objects.filter(Q(subject__classroom=student.classroom) & Q(subject__school = student.school))
    
class StudentResultView(generics.ListAPIView):
    serializer_class = serializers.ResultListSerializer
    permission_classes = [IsAuthenticated & StudentLevelPermission & ~AdminPermission & IsTokenValid]
    
    def get_queryset(self):
        student = models.StudentModel.objects.get(user=self.request.user)
        return models.ResultModel.objects.filter(student=student)
    
