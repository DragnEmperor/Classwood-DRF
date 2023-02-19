from django.contrib import admin
from . import models
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
    
class StudentAdmin(ModelAdmin):
    list_display = ("full_name","classroom","school")
    list_filter = ("classroom","subjects","school")
    
class AttendanceAdmin(ModelAdmin):
    list_display = ("student","date","present",)
    list_filter = ("student","date","present",)
        
admin.site.register(models.SchoolModel,SchoolAdmin)
admin.site.register(models.StaffModel,StaffAdmin)
admin.site.register(models.Accounts,AccountsAdmin)
admin.site.register(models.ClassroomModel,ClassroomAdmin)
admin.site.register(models.BlackListedToken)
admin.site.register(models.Subject,SubjectAdmin)
admin.site.register(models.StudentModel,StudentAdmin)
admin.site.register(models.Attendance,AttendanceAdmin)
admin.site.register(models.Notice)
admin.site.register(models.Attachment)
# Register your models here.
