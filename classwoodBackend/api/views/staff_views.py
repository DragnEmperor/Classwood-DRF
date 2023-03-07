from rest_framework import generics,status,viewsets,mixins
from rest_framework.response import Response
from .. import models
from ..permissions import AdminPermission,StaffLevelPermission,IsTokenValid,ReadOnlyStaffPermission,ReadOnlyStudentPermission
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema,OpenApiParameter,OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .. import serializers
from django.shortcuts import get_object_or_404
from django.utils import timezone
import csv

class StaffSingleView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.StaffListSerializer
    permission_classes = [IsAuthenticated & StaffLevelPermission & ~AdminPermission & IsTokenValid]
    
    def get_object(self):
        staff = models.StaffModel.objects.get(user=self.request.user)
        staff.user.password = None
        return staff
    
    def patch(self, request):
        data = request.data.copy()
        staff = self.get_object()
        if data.get('user') is not None:
            return Response(data={"message":"Account credentials cannot be changed. Contact Administrator"},status=status.HTTP_200_OK)
        if data.get('school') is not None:
            return Response(data={"message":"School cannot be changed. Contact Administrator"},status=status.HTTP_200_OK)
        serializer = self.serializer_class(staff,data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)
    
class ClassroomStaffView(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.ClassroomCreateSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = models.ClassroomModel.objects.all()
    
    def get_queryset(self):
        # # for displaying all classrooms to class-teachers and sub-class-teachers
        # classroom = models.ClassroomModel.objects.filter(class_teacher=models.StaffModel.objects.get(user=self.request.user))
        # classroom2 = models.ClassroomModel.objects.filter(sub_class_teacher=models.StaffModel.objects.get(user=self.request.user))
        # # for displaying classes of teachers who just teach subjects.
        # teaches = models.Subject.objects.filter(teacher=models.StaffModel.objects.get(user=self.request.user))
        # classroom3 = models.ClassroomModel.objects.filter(id=teaches.classroom.id)
        # return classroom | classroom2 | classroom3
        teacher = get_object_or_404(models.StaffModel,user=self.request.user)
        classroom = models.ClassroomModel.objects.filter(Q(class_teacher=teacher) | Q(sub_class_teacher=teacher))
        teaches = list(models.Subject.objects.only("classroom").filter(teacher=teacher).values_list('classroom', flat=True))
        classroom2 = models.ClassroomModel.objects.filter(id__in=teaches)
        return classroom | classroom2
    
class SubjectCreateView(viewsets.ModelViewSet):
    serializer_class = serializers.SubjectCreateSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = models.Subject.objects.all()
    
    # @extend_schema(
    #     parameters=OpenApiParameter('classroom',OpenApiTypes.UUID),
    #     examples = [
    #      OpenApiExample(
    #         'Valid example 1',
    #         summary='short summary',
    #         description='longer description',
    #         value={
    #             'songs': {'top10': True},
    #             'single': {'top10': True}
    #         },)
    # ],methods=['GET'])
    
    def get_queryset(self):
        get_classroom = self.request.GET.get('classroom',None)
        teacher = models.StaffModel.objects.filter(user=self.request.user).exists()
        if not teacher and not get_classroom:
            return models.Subject.objects.all()
        if get_classroom is not None:
            return models.Subject.objects.filter(classroom=get_classroom)
        teacher = models.StaffModel.objects.get(user=self.request.user)
        classroom = models.ClassroomModel.objects.get(Q(class_teacher=teacher) | Q(sub_class_teacher=teacher))
        if str(get_classroom) == str(classroom.id):
            return models.Subject.objects.filter(classroom=classroom)
        subjects = models.Subject.objects.filter(teacher=teacher)
        return subjects
    
    def get_serializer_class(self):
        if self.action=='list':
            return serializers.SubjectListSerializer
        return self.serializer_class
    
    def create(self, request):
        data = request.data.copy()
        user = request.user
        school = models.SchoolModel.objects.get(user=user)
         
        # code for getting school of staff (if teacher creates subject)
        # if models.StaffModel.objects.filter(user=user).exists():
        #     school = models.StaffModel.objects.get(user=user).school
        
        data['school'] = school
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Subject Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        
        return Response(data=serializer.errors,status=status.HTTP_200_OK)
    
# class StudentCreateViewset(viewsets.GenericViewSet,mixins.CreateModelMixin):
#     pass

class StudentCreateView(viewsets.ModelViewSet):
    serializer_class = serializers.StudentCreateSerializer
    queryset = models.StudentModel.objects.all()
    permission_classes = [(ReadOnlyStaffPermission | AdminPermission) & IsAuthenticated & IsTokenValid]
    
    def get_serializer_class(self):
        if self.action =='list':
            return serializers.StudentListSerializer
        return self.serializer_class
    
    def destroy(self, request, *args, **kwargs):
        id = self.kwargs['pk']
        student = get_object_or_404(models.Accounts, id=id)
        student.delete()
        return Response(status=204)
    
    def get_queryset(self):
        get_classroom = self.request.GET.get('classroom',None)
        if get_classroom is None:
            students = self.queryset.all()
        else:
            students = models.StudentModel.objects.filter(classroom=get_classroom)
        for student in students:
            student.user.password = None
        return students

    def create(self, request):
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
               data['father_name'] = row.get('Father Name',None)
               data['mother_name'] = row.get('Mother Name',None)
               data['date_of_birth'] = row.get('DOB',None)
               data['gender'] = '1' if row.get('Gender',None)=='M' else '2' if row.get('Gender',None)=='F' else '3'
               data['contact_email'] = row.get('Email',None)
               data['parent_mobile_number'] = row.get('Mobile',None)
               data['address'] = row.get('Address',None)
               data['roll_no'] = row.get('Roll No',None)
               data['admission_no'] = row.get('Admission No',None)
               data['parent_account_no'] = row.get('Account_no',None)
               data['date_of_admission'] = row.get('Date of Admission',None)
               className = row.get('Class',None)
               section = row.get('Section',None)
               classroom = models.ClassroomModel.objects.get(class_name=className,section_name=section)
               data['classroom'] = classroom.id
               school = models.SchoolModel.objects.get(user=request.user)
               data['school'] = school
               get_subjects = row.get('Subject',None)
               subjects=[]
               if get_subjects is not None:
                 get_subjects = get_subjects.split(',')
                 for s in get_subjects:
                   try:
                     subject = models.Subject.objects.get(name=s,classroom=classroom)
                     subjects.append(subject.id)
                   except models.Subject.DoesNotExist:
                        errors.append({
                        'row': row_num,
                        'errors': {"Subject(s) not found in classroom"}
                    })
               else:
                   subjects = models.Subject.objects.filter(classroom=classroom).values_list('id',flat=True)
               data['subjects'] = subjects
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
                return Response(data={"message":"Student Added from CSV Successfully"},status=status.HTTP_201_CREATED)
        else:
           data = request.data.copy()
           school = models.SchoolModel.objects.get(user=request.user)
           data['school'] = school
           subjects = data.get('subjects')
           if subjects is not None:
            for subject in subjects:
              if not models.Subject.objects.filter(classroom=data.get('classroom'),id=subject).exists():
                return Response(data={"message": "Subject(s) not found in classroom"},status=status.HTTP_200_BAD_REQUEST)
           else:
               subjects = models.Subject.objects.filter(classroom=data.get('classroom')).values_list('id',flat=True)
           serializer = self.serializer_class(data=data)
           if serializer.is_valid():
             serializer.save()
             response = {"message": "Student Created Successfully", "data": serializer.data}
             return Response(data=response,status=status.HTTP_201_CREATED)
           return Response(data=serializer.errors,status=status.HTTP_200_OK)
    
    
class AttendanceView(viewsets.ModelViewSet):
    serializer_class = serializers.AttendanceSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = models.Attendance.objects.all()
    
    def get_serializer_class(self):
        if self.action=='list':
            return serializers.AttendanceListSerializer
        return self.serializer_class
    
    def create(self, request):
        data = request.data.copy()
        user = request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        data['school'] = school
        student_class = (models.StudentModel.objects.get(user=data.get('student'))).classroom.id
        if str(data.get('classroom')) != str(student_class):
            return Response(data={"message": "Classroom does not match with student's classroom"},status=status.HTTP_200_OK)
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Attendance Marked Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)
    
class ExamView(viewsets.ModelViewSet):
    serializer_class = serializers.ExamCreateSerializer 
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = models.ExamModel.objects.all()
    
    def get_serializer_class(self):
        if self.action=='list':
            return serializers.ExamListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        get_classroom = self.request.GET.get('classroom',None)
        if get_classroom is None:
            exams = self.queryset.all()
        else:
            exams = models.ExamModel.objects.filter(classroom=get_classroom)
        return exams
    
    
    def create(self, request):
      data = request.data.copy()
      serializer = self.serializer_class(data=data)
      if serializer.is_valid():
            serializer.save()
            response = {"message": "Exam Added Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
      return Response(data=serializer.errors,status=status.HTTP_200_OK) 
  
class ResultView(viewsets.ModelViewSet):
    serializer_class = serializers.ResultSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission | ReadOnlyStudentPermission) & IsTokenValid]
    queryset = models.ResultModel.objects.all()
    
    def get_queryset(self):
        get_student = self.request.GET.get('student',None)
        if get_student is None:
            results = self.queryset.all()
        else:
            results = models.ResultModel.objects.filter(student=get_student)
        return results
    
    def create(self, request):
        data = request.data.copy()
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Result Added Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)

    
    
    
    
    
    

    
    

