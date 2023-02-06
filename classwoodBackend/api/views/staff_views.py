from rest_framework import generics,status,viewsets
from rest_framework.response import Response
from ..models import SchoolModel,StaffModel,ClassroomModel
from ..serializers import StaffProfileSerializer,ClassroomCreateSerializer
from ..permissions import AdminPermission,StaffLevelPermission,IsTokenValid
    
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
    

    
    

