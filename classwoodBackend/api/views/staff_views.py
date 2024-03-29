from rest_framework import generics,status,viewsets
from rest_framework.response import Response
from .. import models
from ..permissions import AdminPermission,StaffLevelPermission,IsTokenValid,ReadOnlyStaffPermission,ReadOnlyStudentPermission
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema,OpenApiParameter,OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .. import serializers
from django.shortcuts import get_object_or_404
from ..utils import generate_staff_user
import csv,datetime
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from django.http import QueryDict,JsonResponse
from django.forms.models import model_to_dict

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
        session = self.request.GET.get('session',None)
        teacher = get_object_or_404(models.StaffModel,user=self.request.user)
        school = teacher.school
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        classroom = models.ClassroomModel.objects.filter(Q(class_teacher=teacher) | Q(sub_class_teacher=teacher),session=session)
        teaches = list(models.Subject.objects.only("classroom").filter(teacher=teacher).values_list('classroom', flat=True))
        classroom2 = models.ClassroomModel.objects.filter(id__in=teaches,session=session)
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
        session = self.request.GET.get('session',None)
        user=self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        teacher = models.StaffModel.objects.filter(user=self.request.user,session=session).exists()
        if not teacher and get_classroom is None:
            return models.Subject.objects.filter(school=school,session=session)
        if not teacher and get_classroom is not None:
            return models.Subject.objects.filter(classroom=get_classroom,school=school,session=session)
        teacher = models.StaffModel.objects.get(user=self.request.user,session=session)
        classrooms = models.ClassroomModel.objects.filter(Q(class_teacher=teacher) | Q(sub_class_teacher=teacher))
        for classroom in classrooms:
            if str(get_classroom) == str(classroom.id):
               return models.Subject.objects.filter(classroom=classroom,school=school,session=session)
        if get_classroom is not None:
          return models.Subject.objects.filter(classroom=get_classroom,teacher=teacher,school=school,session=session)
        return models.Subject.objects.filter(teacher=teacher,school=school,session=session)

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
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
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
        school = student.school
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
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
        session = self.request.GET.get('session',None)
        user = self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        if get_classroom is None:
            students = models.StudentModel.objects.filter(school = school,session=session)
        else:
            students = models.StudentModel.objects.filter(classroom=get_classroom,school = school,session=session)
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
            session = request.data.get('session',None)
            for row_num, row in enumerate(reader, 1):
               if not all(row.values()):
                    break
               data['first_name'] = row.get('First Name',None)
               data['last_name'] = row.get('Last Name',None)
               data['father_name'] = row.get('Father Name',None)
               data['mother_name'] = row.get('Mother Name',None)
               dob = row.get('DOB',None)
               try:
                   dob = datetime.datetime.strptime(dob,'%Y-%m-%d')
               except ValueError:
                   dob = datetime.datetime.strptime(dob,'%d-%m-%Y')
               dob = dob.strftime('%Y-%m-%d')
               data['date_of_birth'] = dob
               data['gender'] = '1' if row.get('Gender',None)=='M' else '2' if row.get('Gender',None)=='F' else '3'
               data['contact_email'] = row.get('Email',None)
               data['parent_mobile_number'] = row.get('Mobile',None)
               data['address'] = row.get('Address',None)
               data['roll_no'] = row.get('Roll No',None)
               data['admission_no'] = row.get('Admission No',None)
               data['parent_account_no'] = row.get('Account_no',None)
               data['session'] = session
               doa = row.get('Date of Admission',None)
               try:
                   doa = datetime.datetime.strptime(doa,'%Y-%m-%d')
               except ValueError:
                   doa = datetime.datetime.strptime(doa,'%d-%m-%Y')
               doa = doa.strftime('%Y-%m-%d')
               data['date_of_admission'] = doa
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
               if(session is None):
                   session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
                   data['session'] = session.id
               get_subjects = row.get('Subjects',None)
               subjects=[]
               if get_subjects is not None:
                 get_subjects = get_subjects.split(',')
                 for s in get_subjects:
                   try:
                     subject = models.Subject.objects.get(name=s,classroom = classroom, session = session)
                     subjects.append(subject.id)
                   except models.Subject.DoesNotExist:
                        errors.append({
                        'row': row_num,
                        'errors': {"Subject(s) not found in classroom"}
                    })
               else:
                   subjects = models.Subject.objects.filter(classroom = classroom, session = session).values_list('id',flat=True)
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
           session = data.get('session',None)
           if session is None:
              session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
              data['session'] = session.id
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
        session = self.request.GET.get('session',None)
        user=self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        if get_classroom is None:
            attendance = models.StudentAttendance.objects.filter(school=school,session=session)
        else:
            attendance = models.StaffAttendance.objects.filter(classroom=get_classroom,school=school,session=session)
        return attendance

    def create(self, request):
        data = request.data.copy()
        user = request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        data['school'] = school
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
        student_class = (models.StudentModel.objects.get(user=data.get('student'),session=session)).classroom.id
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
        session = self.request.GET.get('session',None)
        user=self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        if get_classroom is None:
            exams = models.ExamModel.objects.filter(school = school,session = session)
        else:
            exams = models.ExamModel.objects.filter(classroom = get_classroom,school = school, session = session)
        return exams


    def create(self, request):
      data = request.data.copy()
      user = request.user
      try:
          school = models.SchoolModel.objects.get(user=user)
      except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
      data['school'] = school
      session = data.get('session',None)
      if session is None:
        session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        data['session'] = session.id
      serializer = self.serializer_class(data=data)
      if serializer.is_valid():
            serializer.save()
            response = {"message": "Exam Added Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
      return Response(data=serializer.errors,status=status.HTTP_200_OK)

class ExamMarkView(generics.UpdateAPIView):
    queryset = models.ExamModel.objects.all()

    def patch(self,request,*args,**kwargs):
        exam = self.get_object()
        exam.is_complete =  request.data.get('is_complete', exam.is_complete)
        exam.save()
        return JsonResponse(data={"exam":model_to_dict(exam),"message":"Exam Marked Successfully"},status=status.HTTP_200_OK)

class ResultView(viewsets.ModelViewSet):
    serializer_class = serializers.ResultSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission | ReadOnlyStudentPermission) & IsTokenValid]
    queryset = models.ResultModel.objects.all()

    def get_serializer_class(self):
        if self.action=='list':
            return serializers.ResultListSerializer
        return self.serializer_class

    def get_queryset(self):
        get_student = self.request.GET.get('student',None)
        get_exam = self.request.GET.get('exam',None)
        session = self.request.GET.get('session',None)
        user = self.request.user
        try:
            school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
            school = (models.StaffModel.objects.get(user=user)).school
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        results = models.ResultModel.objects.filter(student__school = school,session=session)
        if get_student is not None:
          results = results.filter(student=get_student,session = session)
        if get_exam is not None:
          results = results.filter(exam=get_exam,session = session)
        if get_student is not None and get_exam is not None:
          results = results.filter(student=get_student, exam=get_exam, session = session)
        return results

    def create(self, request):
        csv_file = request.FILES.get('csv_file',None)
        user = request.user
        if csv_file:
            data = {}
            errors=[]
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            classroom = request.data.get('classroom',None)
            session = request.data.get('session',None)
            for row_num, row in enumerate(reader, 1):
               if not all(row.values()):
                    break
            #    name = row.get('First Name',None) + row.get('Last Name',None)
               rollNo = row.get('Roll No',None)
               try:
                 school = models.SchoolModel.objects.get(user=user)
               except models.SchoolModel.DoesNotExist:
                 school = (models.StaffModel.objects.get(user=user)).school
               if session is None:
                   session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
                   data['session'] = session.id
               if classroom is None :
                  className = row.get('Class',None) + row.get('Section')
                  classroom = models.ClassroomModel.objects.get(class_name=className,school=school,session=session)
               student = models.StudentModel.objects.get(roll_no=rollNo,classroom=classroom,session=session)
               if models.StaffModel.objects.filter(user=self.request.user,session=session).exists():
                   teacher = models.StaffModel.objects.get(user=request.user,session=session)
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
           try:
             school = models.SchoolModel.objects.get(user=user)
           except models.SchoolModel.DoesNotExist:
             school = (models.StaffModel.objects.get(user=user)).school
           data['school'] = school
           session = data.get('session',None)
           if session is None:
              session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
              data['session'] = session.id
           serializer = self.serializer_class(data=data)
           if serializer.is_valid():
             serializer.save()
             response = {"message": "Result Created Successfully", "data": serializer.data}
             return Response(data=response,status=status.HTTP_201_CREATED)
           return Response(data=serializer.errors,status=status.HTTP_200_OK)


class TimeTableView(viewsets.ModelViewSet):
    serializer_class = serializers.TimeTableSerializer
    permission_classes = [IsAuthenticated & (ReadOnlyStaffPermission | ReadOnlyStudentPermission | AdminPermission) & IsTokenValid]
    queryset = models.TimeTableModel.objects.all()

    def get_serializer_class(self):
        if self.action=='list':
            return serializers.TimeTableListSerializer
        return self.serializer_class

    def get_queryset(self):
        get_classroom = self.request.GET.get('classroom',None)
        session = self.request.GET.get('session',None)
        user = self.request.user
        try:
            school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
            school = (models.StaffModel.objects.get(user=user)).school
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        if get_classroom is None:
            timetable = models.TimeTableModel.objects.filter(school=school,session=session)
        else:
            timetable = models.TimeTableModel.objects.filter(classroom=get_classroom,school=school,session=session)
        return timetable

    def create(self, request):
        data = request.data.copy()
        user = request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        data['school'] = school
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
        timetable = data.get('timetable',None)
        if timetable is None:
            return Response(data={"message":"Timetable is required"},status=status.HTTP_200_OK)
        # timeInfo = timetable[1]
        # subjects_days = timetable[0]
        classroom = data.get('classroom',None)
        if classroom is None:
            return Response(data={"message":"Classroom is required"},status=status.HTTP_200_OK)
        for i in range(0,6):
            day_table={}
            errors=[]
            print('i',i)
            for j in range(0,len(timetable[i])):
                print('j',j)
                # start_time = timeInfo[j]['start'].hour +":" + timeInfo[j]['start'].minute + ":00"
                # end_time = timeInfo[j]['end'].hour +":" + timeInfo[j]['end'].minute + ":00"
                if(timetable[i][j]['subject']['name'] != "No Subject Selected"):
                    day_table['day'] = i
                    day_table['start_time'] = str(timetable[i][j]['start']['hour']) +":" + str(timetable[i][j]['start']['minute']) + ":00"
                    day_table['end_time'] = str(timetable[i][j]['end']['hour']) +":" + str(timetable[i][j]['end']['minute']) + ":00"
                    day_table['subject'] = timetable[i][j]['subject']['id']
                    day_table['teacher'] = timetable[i][j]['subject']['teacher_id']
                    day_table['school'] = data['school']
                    day_table['classroom'] = data['classroom']
                    day_table['session'] = data['session']
                    serializer = self.serializer_class(data=day_table)
                    if serializer.is_valid():
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



class CommonTimeView(viewsets.ModelViewSet):
    serializer_class = serializers.CommonTimeSerializer
    permission_classes = [IsAuthenticated & (ReadOnlyStaffPermission | ReadOnlyStudentPermission | AdminPermission) & IsTokenValid]
    queryset = models.CommonTimeModel.objects.all()

    def get_serializer_class(self):
        if self.action=='list':
            return serializers.CommonTimeListSerializer
        return self.serializer_class

    def get_queryset(self):
        get_classroom = self.request.GET.get('classroom',None)
        session = self.request.GET.get('session',None)
        user = self.request.user
        try:
            school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
            school = (models.StaffModel.objects.get(user=user)).school
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        if get_classroom is None:
            timetable = models.CommonTimeModel.objects.filter(school=school,session=session)
        else:
            timetable = models.CommonTimeModel.objects.filter(classroom=get_classroom,school=school,session=session)
        return timetable

    def create(self, request):
        data = request.data.copy()
        user = request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        data['school'] = school
        common = data.get('common',None)
        session = data.get('session',None)
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
        errors = []
        classroom = data.get('classroom',None)
        if classroom is None:
            return Response(data={"message":"Classroom is required"},status=status.HTTP_200_OK)

        if common :
            for i in range(0, len(common)):
                print(common[i])
                day_table = {}
                day_table['start_time'] = str(common[i]['start']['hour']) +":" + str(common[i]['start']['minute']) + ":00"
                day_table['end_time'] = str(common[i]['end']['hour']) +":" + str(common[i]['end']['minute']) + ":00"
                day_table['subject'] = common[i]['subject']
                day_table['school'] = data['school']
                day_table['classroom'] = data['classroom']
                day_table['session'] = data['session']
                serializer = self.serializer_class(data=day_table)
                if serializer.is_valid():
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
            return Response(data={"message":"Common Time Added Successfully"},status=status.HTTP_201_CREATED)


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
        session = self.request.GET.get('session',None)
        user=self.request.user
        try:
          school = models.SchoolModel.objects.get(user=user)
        except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
        if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
        if get_classroom is None:
            try:
                teacher = models.StaffModel.objects.get(user=user)
                classroom = models.ClassroomModel.objects.filter(Q(class_teacher=teacher) | Q(sub_class_teacher=teacher),session=session)
                teaches = list(models.Subject.objects.only("classroom").filter(teacher=teacher,session=session).values_list('classroom', flat=True))
                classroom2 = models.ClassroomModel.objects.filter(id__in=teaches,session=session)
                total_classes = classroom | classroom2
                syllabus = models.SyllabusModel.objects.none()
                for classroom in total_classes:
                   class_syll = models.SyllabusModel.objects.filter(classroom = classroom,school=school,session=session)
                   syllabus = syllabus | class_syll
            except models.StaffModel.DoesNotExist:
                syllabus = models.SyllabusModel.objects.filter(school = school,session=session)
        else:
            syllabus = models.SyllabusModel.objects.filter(classroom = get_classroom,school = school, session = session)
        return syllabus

    def create(self, request):
      data = request.data.copy()
      user = request.user
      try:
          school = models.SchoolModel.objects.get(user=user)
      except models.SchoolModel.DoesNotExist:
          school = (models.StaffModel.objects.get(user=user)).school
      subject_id = data.get('subject',None)
      try:
          subject = models.Subject.objects.get(id=subject_id,classroom=data.get('classroom',None),school=school)
      except models.Subject.DoesNotExist:
          return Response(data={"message":"Subject does not exists."},status=status.HTTP_200_OK)
      data['school'] = school
      print(data)
      session = data.get('session',None)
      if session is None:
            session = models.SessionModel.objects.filter(school=school,is_active=True).order_by('-start_date').first()
            data['session'] = session.id
      serializer = self.serializer_class(data=data)
      if serializer.is_valid():
            serializer.save()
            response = {"message": "Syllabus Added Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
      return Response(data=serializer.errors,status=status.HTTP_200_OK)


