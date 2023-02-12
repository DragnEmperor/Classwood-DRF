from rest_framework import generics,status,viewsets,mixins
from rest_framework.response import Response
from .. import models
from ..permissions import AdminPermission,StaffLevelPermission,IsTokenValid,RestrictedStaffPermission
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema,OpenApiParameter,OpenApiExample
from drf_spectacular.types import OpenApiTypes
from .. import serializers
from django.shortcuts import get_object_or_404

class StaffSingleView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.StaffProfileSerializer
    permission_classes = [IsAuthenticated & StaffLevelPermission & ~AdminPermission & IsTokenValid]
    
    def get_object(self):
        staff = models.StaffModel.objects.get(user=self.request.user)
        staff.user.password = None
        return staff
    
    def patch(self, request):
        data = request.data
        staff = self.get_object()
        if data.get('user') is not None:
            return Response(data={"message":"Account credentials cannot be changed. Contact Administrator"},status=status.HTTP_400_BAD_REQUEST)
        if data.get('school') is not None:
            return Response(data={"message":"School cannot be changed. Contact Administrator"},status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(staff,data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
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
        get_classroom = self.request.data.get('classroom')
        teacher = models.StaffModel.objects.filter(user=self.request.user).exists()
        if not teacher:
            return models.Subject.objects.all()
        teacher = models.StaffModel.objects.get(user=self.request.user)
        classroom = models.ClassroomModel.objects.get(Q(class_teacher=teacher) | Q(sub_class_teacher=teacher))
        if str(get_classroom) == str(classroom.id):
            return models.Subject.objects.filter(classroom=classroom)
        subjects = models.Subject.objects.filter(teacher=teacher)
        return subjects
    
    def create(self, request):
        data = request.data
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
        
        return Response(data=serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
# class StudentCreateViewset(viewsets.GenericViewSet,mixins.CreateModelMixin):
#     pass

class StudentCreateView(viewsets.ModelViewSet):
    serializer_class = serializers.StudentCreateSerializer
    queryset = models.StudentModel.objects.all()
    permission_classes = [(RestrictedStaffPermission | AdminPermission) & IsAuthenticated & IsTokenValid]
    
    def get_serializer_class(self):
        if self.action =='list':
            return serializers.StudentReadSerializer
        return self.serializer_class
    
    def get_object(self):
        serializer_class = self.get_serializer_class()
        return super().get_object()
    
    def destroy(self, request, *args, **kwargs):
        id = self.kwargs['pk']
        student = get_object_or_404(models.Accounts, id=id)
        student.delete()
        return Response(status=204)
    
    def get_queryset(self):
        serializer_class = self.get_serializer_class()
        get_classroom = self.request.data.get('classroom')
        if get_classroom is None:
            students = models.StudentModel.objects.all()
        else:
            students = models.StudentModel.objects.filter(className=get_classroom)
        for student in students:
            student.user.password = None
        return students

    def create(self, request):
        data = request.data
        user = request.user
        school = models.SchoolModel.objects.get(user=user)
        data['school'] = school
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Student Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        return Response(data=serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    
    
    
    
    
    

    
    

