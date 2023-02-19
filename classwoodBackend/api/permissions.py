from rest_framework import permissions
from .models import SchoolModel,StaffModel,BlackListedToken,StudentModel

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
    
class StudentLevelPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return StudentModel.objects.filter(user=request.user).exists()
    


class ReadOnlyStaffPermission(StaffLevelPermission):
     def has_permission(self, request, view):
        return ((view.action == 'list' or view.action=='retrieve') and super(ReadOnlyStaffPermission, self).has_permission(request, view))
# class ActionBasedPermission(permissions.AllowAny):
#     """
#     Grant or deny access to a view, based on a mapping in view.action_permissions
#     """
#     def has_permission(self, request, view):
#         for klass, actions in getattr(view, 'action_permissions', {}).items():
#             print('view',view.action)
#             print('view',actions)
#             print('view',klass)
#             if view.action in actions:
#                 print('ran')
#                 return klass().has_permission(request, view)
#         return False
    
