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
from ..utils import generate_staff_user
import csv
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from django.http import QueryDict

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
    
    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.ClassroomListSerializer
        return self.serializer_class
    
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
        user=self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        teacher = models.StaffModel.objects.filter(user=self.request.user).exists()
        if not teacher and not get_classroom:
            return models.Subject.objects.filter(school=school)
        if get_classroom is not None:
            return models.Subject.objects.filter(classroom=get_classroom,school=school)
        teacher = models.StaffModel.objects.get(user=self.request.user)
        classroom = models.ClassroomModel.objects.get(Q(class_teacher=teacher) | Q(sub_class_teacher=teacher))
        if str(get_classroom) == str(classroom.id):
            return models.Subject.objects.filter(classroom=classroom,school=school)
        subjects = models.Subject.objects.filter(teacher=teacher,school=school)
        return subjects
    
    def get_serializer_class(self):
        if self.action=='list':
            return serializers.SubjectListSerializer
        return self.serializer_class
    
    def create(self, request):
        data = request.data.copy()
        school = models.SchoolModel.objects.get(user=request.user)
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
    parser_classes = [MultiPartParser,FormParser,JSONParser]
    
    def get_serializer_class(self):
        if self.action =='list':
            return serializers.StudentListSerializer
        return self.serializer_class
    
    def destroy(self, request, *args, **kwargs):
        id = self.kwargs['pk']
        student = get_object_or_404(models.Accounts, id=id)
        student.delete()
        return Response(status=204)
    
    def partial_update(self, request,*args,**kwargs):
        id=self.kwargs['pk']
        data=request.data.copy()
        student = self.get_object()
        f_name = data.get('first_name',student.first_name)  
        pm = data.get('parent_mobile_number',student.parent_mobile_number)
        doa = data.get('date_of_admission',student.date_of_admission)  
        if f_name != student.first_name or pm != student.parent_mobile_number or doa != student.date_of_admission:
            newAccount = generate_staff_user(f_name,pm,doa)
            user = student.user
            user.email = newAccount['email']
            user.set_password(newAccount['password'])
            user.save() 
        serializer = self.get_serializer(student, data=data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(data=serializer.data,status=status.HTTP_200_OK)
        return Response(data=serializer.errors,status=status.HTTP_200_OK)
        
    
    def get_queryset(self):
        get_classroom = self.request.GET.get('classroom',None)
        user = self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if get_classroom is None:
            students = models.StudentModel.objects.filter(school = school)
        else:
            students = models.StudentModel.objects.filter(classroom=get_classroom,school = school)
        for student in students:
            student.user.password = None
        return students

    def create(self, request):
        csv_file = request.FILES.get('csv_file',None)
        data = {}
        errors=[]
        if csv_file:
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(decoded_file)
            classroom = request.data.get('classroom',None)
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
               try:
                  if classroom is None:
                    className = row.get('Class',None)
                    section = row.get('Section',None)
                    classroom = models.ClassroomModel.objects.get(class_name=className,section_name=section)
                    data['classroom'] = classroom.id
                  else:
                    data['classroom'] = classroom
               except models.ClassroomModel.DoesNotExist:
                  return Response(data={"message":"Classroom not found"},status=status.HTTP_400_BAD_REQUEST)
               school = models.SchoolModel.objects.get(user=request.user)
               data['school'] = school
               get_subjects = row.get('Subjects',None)
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
           subjects = data.get('subjects',None)
           if subjects is not None:
            for subject in subjects:
              if not models.Subject.objects.filter(classroom=data.get('classroom'),id=subject).exists():
                return Response(data={"message": "Subject(s) not found in classroom"},status=status.HTTP_200_BAD_REQUEST)
           else:
               subjects = models.Subject.objects.filter(classroom=data.get('classroom')).values_list('id',flat=True)
            #    subjects = [str(subject.id) for subject in models.Subject.objects.filter(classroom=data.get('classroom'))]
           if(isinstance(request.data,QueryDict)):
               data.setlist('subjects',subjects)
           else:
            data['subjects'] = subjects
           serializer = self.get_serializer(data=data)
           if serializer.is_valid():
             serializer.save()
             response = {"message": "Student Created Successfully", "data": serializer.data}
             return Response(data=response,status=status.HTTP_201_CREATED)
           return Response(data=serializer.errors,status=status.HTTP_200_OK)
    
    
class StudentAttendanceView(viewsets.ModelViewSet):
    serializer_class = serializers.StudentAttendanceSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = models.StudentAttendance.objects.all()
    
    def get_serializer_class(self):
        if self.action=='list':
            return serializers.StudentAttendanceListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        get_classroom = self.request.GET.get('classroom',None)
        user=self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if get_classroom is None:
            attendance = models.StudentAttendance.objects.filter(school=school)
        else:
            attendance = models.StaffAttendance.objects.filter(classroom=get_classroom,school=school)
        return attendance
    
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
            response = {"message": "Student Attendance Marked Successfully", "data": serializer.data}
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
        user=self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if get_classroom is None:
            exams = models.ExamModel.objects.filter(school = school)
        else:
            exams = models.ExamModel.objects.filter(classroom = get_classroom,school = school)
        return exams
    
    
    def create(self, request):
      data = request.data.copy()
      school = models.SchoolModel.objects.get(user=request.user)
      data['school'] = school
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
        user = self.request.user
        school = models.SchoolModel.objects.get(user=user)
        if get_student is None:
            results = results = models.ResultModel.objects.filter(student__school = school)
        else:
            results = models.ResultModel.objects.filter(student=get_student,student__school = school)
        return results
    
    def create(self, request):
        csv_file = request.FILES.get('csv_file',None)
        if csv_file:
            data = {}
            errors=[]
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            classroom = request.data.get('classroom',None)
            for row_num, row in enumerate(reader, 1):
               if not all(row.values()):
                    break
            #    name = row.get('First Name',None) + row.get('Last Name',None)
               rollNo = row.get('Roll No',None)
               school = models.SchoolModel.objects.get(user=request.user)
               if classroom is None :
                  className = row.get('Class',None) + row.get('Section')
                  classroom = models.ClassroomModel.objects.get(class_name=className,school=school)
               student = models.StudentModel.objects.get(roll_no=rollNo,classroom=classroom)
               if models.StaffModel.objects.filter(user=self.request.user).exists():
                   teacher = models.StaffModel.objects.get(user=request.user)
                   if teacher not in classroom.teachers.all():
                       return Response(data={"message": "Teacher not assigned to classroom"},status=status.HTTP_200_OK)
               data['school'] = school
               data['exam'] = request.data.get('exam')
               data['student'] = student
               data['score'] = row.get('Marks',None)
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
                return Response(data={"message":"Result Added from CSV Successfully"},status=status.HTTP_201_CREATED)
        else:
           data = request.data.copy()
           school = models.SchoolModel.objects.get(user=request.user)
           data['school'] = school
           serializer = self.serializer_class(data=data)
           if serializer.is_valid():
             serializer.save()
             response = {"message": "Result Created Successfully", "data": serializer.data}
             return Response(data=response,status=status.HTTP_201_CREATED)
           return Response(data=serializer.errors,status=status.HTTP_200_OK)
       
       
class TimeTableView(viewsets.ModelViewSet):
    serializer_class = serializers.TimeTableSerializer
    permission_classes = [IsAuthenticated & (ReadOnlyStaffPermission | AdminPermission) & IsTokenValid]
    queryset = models.TimeTableModel.objects.all()
    
    def get_serializer_class(self):
        if self.action=='list':
            return serializers.TimeTableListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        get_classroom = self.request.GET.get('classroom',None)
        user = self.request.user
        school = models.SchoolModel.objects.get(user=user)
        if get_classroom is None:
            timetable = models.TimeTableModel.objects.filter(school=school)
        else:
            timetable = models.TimeTableModel.objects.filter(classroom=get_classroom,school=school)
        return timetable
    
    def create(self, request):
        data = request.data.copy()
        user = request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        data['school'] = school
        timetable = data.get('timetable',None)
        if timetable is None:
            return Response(data={"message":"Timetable is required"},status=status.HTTP_200_OK)
        timeInfo = timetable[1]
        subjects_days = timetable[0]
        classroom = data.get('classroom',None)
        if classroom is None:
            return Response(data={"message":"Classroom is required"},status=status.HTTP_200_OK)
        for i in range(0,6):
            day_table={}
            errors=[]
       
            print(i)
            for j in range(0,len(timeInfo)):
                print(j)
                # start_time = timeInfo[j]['start'].hour +":" + timeInfo[j]['start'].minute + ":00"
                # end_time = timeInfo[j]['end'].hour +":" + timeInfo[j]['end'].minute + ":00"
                if(subjects_days[j][i]['id']):
                    day_table['day'] = i
                    day_table['start_time'] = timeInfo[j]['start']['hour'] +":" + timeInfo[j]['start']['minute'] + ":00"
                    day_table['end_time'] = timeInfo[j]['end']['hour'] +":" + timeInfo[j]['end']['minute'] + ":00"
                    day_table['subject'] = subjects_days[j][i]['id']
                    day_table['teacher'] = subjects_days[j][i]['teacher_id']
                    day_table['school'] = data['school']
                    day_table['classroom'] = data['classroom']
                    serializer = self.serializer_class(data=day_table)
                    print("this is ser",day_table, serializer.is_valid())
                    if serializer.is_valid():
                        print("\n\n\n\n\n serialzie")
                        serializer.save()
                        print("save passes")
                        pass
                    else:
                        errors.append({
                        'row': i,
                        'errors': serializer.errors
                    })
        if errors:  
            return Response(data=errors,status=status.HTTP_200_OK)
        else:
            return Response(data={"message":"TimeTable Added Successfully"},status=status.HTTP_201_CREATED)
            
    
class SyllabusView(viewsets.ModelViewSet):
    serializer_class = serializers.SyllabusSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = models.SyllabusModel.objects.all()
    
    def get_serializer_class(self):
        if self.action=='list':
            return serializers.SyllabusListSerializer
        return self.serializer_class
    
    def get_queryset(self):
        get_classroom = self.request.GET.get('classroom',None)
        user=self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if get_classroom is None:
            syllabus = models.SyllabusModel.objects.filter(school = school)
        else:
            syllabus = models.SyllabusModel.objects.filter(classroom = get_classroom,school = school)
        return syllabus
    
    def create(self, request):
      data = request.data.copy()
      school = models.SchoolModel.objects.get(user=request.user)
      data['school'] = school
      print(data)
      serializer = self.serializer_class(data=data)
      if serializer.is_valid():
            serializer.save()
            response = {"message": "Syllabus Added Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
      return Response(data=serializer.errors,status=status.HTTP_200_OK) 

    
