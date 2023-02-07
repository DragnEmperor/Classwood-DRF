from rest_framework import generics,status,viewsets
from rest_framework.response import Response
from ..models import SchoolModel,StaffModel,ClassroomModel,Subject
from ..serializers import StaffProfileSerializer,ClassroomCreateSerializer,SubjectCreateSerializer
from ..permissions import AdminPermission,StaffLevelPermission,IsTokenValid
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

class StaffSingleView(generics.RetrieveUpdateAPIView):
    serializer_class = StaffProfileSerializer
    permission_classes = [IsAuthenticated & StaffLevelPermission & ~AdminPermission & IsTokenValid]
    
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
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = ClassroomModel.objects.all()
    
    def get_queryset(self):
        # for displaying all classrooms to class-teachers and sub-class-teachers
        classroom = ClassroomModel.objects.filter(class_teacher=StaffModel.objects.get(user=self.request.user))
        classroom2 = ClassroomModel.objects.filter(sub_class_teacher=StaffModel.objects.get(user=self.request.user))
        # for displaying classes of teachers who just teach subjects.
        teaches = Subject.objects.get(teacher=StaffModel.objects.get(user=self.request.user))
        classroom3 = ClassroomModel.objects.filter(id=teaches.classroom.id)
        return classroom | classroom2 | classroom3
    
class SubjectCreateView(viewsets.ModelViewSet):
    serializer_class = SubjectCreateSerializer
    permission_classes = [IsAuthenticated & (StaffLevelPermission | AdminPermission) & IsTokenValid]
    queryset = Subject.objects.all()
    
    def get_queryset(self):
        get_classroom = self.request.data.get('classroom')
        teacher = StaffModel.objects.filter(user=self.request.user).exists()
        if not teacher:
            return Subject.objects.none()
        teacher = StaffModel.objects.get(user=self.request.user)
        classroom = ClassroomModel.objects.get(Q(class_teacher=teacher) | Q(sub_class_teacher=teacher))
        if str(get_classroom) == str(classroom.id):
            return Subject.objects.filter(classroom=classroom)
        subjects = Subject.objects.filter(teacher=teacher)
        return subjects
    
    def create(self, request):
        data = request.data
        user = request.user
        school = SchoolModel.objects.get(user=user)
        data['school'] = school
        
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            response = {"message": "Subject Created Successfully", "data": serializer.data}
            return Response(data=response,status=status.HTTP_201_CREATED)
        
        return Response(data=serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
    
    

    
    

