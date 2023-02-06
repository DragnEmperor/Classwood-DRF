from rest_framework import permissions
from .models import SchoolModel,StaffModel,BlackListedToken

class AdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        school = SchoolModel.objects.filter(user=request.user).exists()
        return school

class IsTokenValid(permissions.BasePermission):
    def has_permission(self, request, view):
        user_id = request.user.id            
        is_allowed_user = True
        token = request.auth
        try:
            is_blackListed = BlackListedToken.objects.get(user=user_id, token=token)
            if is_blackListed:
                is_allowed_user = False
        except BlackListedToken.DoesNotExist:
            is_allowed_user = True
        return is_allowed_user
    
    
class StaffLevelPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        staff = StaffModel.objects.filter(user=request.user).exists()
        return staff
    
