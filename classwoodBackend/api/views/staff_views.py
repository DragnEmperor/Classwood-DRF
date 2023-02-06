from rest_framework import generics,status,viewsets
from rest_framework.response import Response
from ..models import SchoolModel,StaffModel,ClassroomModel,Subject
from ..serializers import StaffProfileSerializer,ClassroomCreateSerializer,SubjectCreateSerializer
from ..permissions import AdminPermission,StaffLevelPermission,IsTokenValid
from django.db.models import Q
    
class StaffSingleView(generics.RetrieveUpdateAPIView):
    serializer_class = StaffProfileSerializer
    permission_classes = [StaffLevelPermission & ~AdminPermission & IsTokenValid]
    
    def get_object(self):
        staff = StaffModel.objects.get(user=self.request.user)
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
    serializer_class = ClassroomCreateSerializer
    permission_classes = [(StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = ClassroomModel.objects.all()
    
    def get_queryset(self):
        classroom = ClassroomModel.objects.filter(class_teacher=StaffModel.objects.get(user=self.request.user))
        classroom2 = ClassroomModel.objects.filter(sub_class_teacher=StaffModel.objects.get(user=self.request.user))
        return classroom | classroom2
    
class SubjectCreateView(viewsets.ModelViewSet):
    serializer_class = SubjectCreateSerializer
    permission_classes = [(StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = Subject.objects.all()
    
    def get_queryset(self):
        classroom = ClassroomModel.objects.filter(Q(class_teacher=StaffModel.objects.get(user=self.request.user)) | Q(sub_class_techer=StaffStaffModel.objects.get(user=self.request.user)))
        if classroom is not None:
            return Subject.objects.filter(classroom=classroom)
        return super().get_queryset()
    
    def create(self, request):
        data = request.data
        # add proper logic for checking school in response
        school = data.get('school')
        if school is None:
            user = request.user
            school = models.SchoolModel.objects.get(user=user)
            data['school'] = school
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Subject Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        
        return Response(data=serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    
    

    
    

