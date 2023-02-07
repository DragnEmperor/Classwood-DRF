from django.contrib import admin
from .models import Accounts,SchoolModel,StaffModel,ClassroomModel,BlackListedToken,Subject
from django.contrib.admin import ModelAdmin

class SchoolAdmin(ModelAdmin):
    list_display = ("user","school_name","school_state")
    
class StaffAdmin(ModelAdmin):
    list_display = ("user","school","first_name","last_name")
    list_filter = ("school",)
    
class AccountsAdmin(ModelAdmin):
    list_display = ("email","id")
    
class ClassroomAdmin(ModelAdmin):
    list_display=("class_name","section_name","class_teacher","school")
    list_filter = ("class_name","class_teacher","school")
    
class SubjectAdmin(ModelAdmin):
    list_display = ("name","classroom","teacher","school")
    list_filter = ("classroom","teacher","school")
        
admin.site.register(SchoolModel,SchoolAdmin)
admin.site.register(StaffModel,StaffAdmin)
admin.site.register(Accounts,AccountsAdmin)
admin.site.register(ClassroomModel,ClassroomAdmin)
admin.site.register(BlackListedToken)
admin.site.register(Subject,SubjectAdmin)
# Register your models here.
