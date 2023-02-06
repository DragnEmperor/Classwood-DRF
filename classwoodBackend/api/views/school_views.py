from django.shortcuts import render
from rest_framework import generics,status,viewsets
# Create your views here.
from .. import serializers
from rest_framework.response import Response
from rest_framework.request import Request
from ..permissions import AdminPermission,StaffLevelPermission,IsTokenValid
from rest_framework.permissions import IsAuthenticated
from .. import models

class SchoolSignUpView(generics.CreateAPIView):
    serializer_class = serializers.SchoolSignUpSerializer
    permission_classes=[]
    def post(self, request: Request):  
        data = request.data  
        serializer = self.serializer_class(data=data)

        if serializer.is_valid():
            serializer.save()
            response = {"message": "School User Created Successfully", "data": serializer.data}
            return Response(data=response, status=status.HTTP_201_CREATED)

        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class SchoolProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.SchoolProfileSerializer
    permission_classes = [IsAuthenticated & AdminPermission & IsTokenValid]
    
    def get_object(self):
        school = models.SchoolModel.objects.get(user=self.request.user)
        school.user.password = None
        return school
    
    def patch(self,request):
        data = request.data
        school = self.get_object()
        serializer = self.serializer_class(school,data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
class StaffView(viewsets.ModelViewSet):
    serializer_class = serializers.StaffCreateSerializer
    permission_classes=[IsAuthenticated & AdminPermission & IsTokenValid]
    queryset = models.StaffModel.objects.all()
     
    def get_queryset(self):
        user = self.request.user
        staff = models.StaffModel.objects.filter(school= models.SchoolModel.objects.get(user=user))
        for items in staff:
            items.user.password = None
        return staff
    
    def create(self,request):
        data = request.data
        # add proper logic for checking school in response
        school = request.data.get('school')
        if school is None:
            user = request.user
            school = models.SchoolModel.objects.get(user=user)
            data['school'] = school
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Staff Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        
        return Response(data=serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
class ClassroomSchoolView(viewsets.ModelViewSet):
    serializer_class = serializers.ClassroomCreateSerializer
    permission_classes=[IsAuthenticated & AdminPermission & IsTokenValid]
    queryset = models.ClassroomModel.objects.all()
     
    def get_queryset(self):
        user = self.request.user
        classroom = models.ClassroomModel.objects.filter(school= models.SchoolModel.objects.get(user=user))
        return classroom
    
    def create(self,request):
        data = request.data
        # add proper logic for checking school in response
        user = request.user
        school = models.SchoolModel.objects.get(user=user)
        data['school'] = school
        class_teacher_account  = models.Accounts.objects.get(id=data.get('class_teacher'))
        sub_teacher_account  = models.Accounts.objects.get(id=data.get('sub_class_teacher'))
        class_teacher = models.StaffModel.objects.get(user=class_teacher_account)
        if class_teacher.is_class_teacher == True:
            return Response(data={"message":"Class Teacher Already Assigned"},status=status.HTTP_400_BAD_REQUEST)
        models.StaffModel.objects.filter(user=class_teacher_account).update(is_class_teacher=True)
        data['class_teacher'] = class_teacher
        data['sub_class_teacher'] = models.StaffModel.objects.get(user=sub_teacher_account)
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Classroom Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        
        return Response(data=serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
        
    
    
    
    
