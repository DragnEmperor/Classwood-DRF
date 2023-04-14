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
    
class StudentAttendanceAdmin(ModelAdmin):
    list_display = ("student","date","present",)
    list_filter = ("student","date","present",)
class StaffAttendanceAdmin(ModelAdmin):
    list_display = ("staff","date","present",)
    list_filter = ("staff","date","present",)
        
admin.site.register(models.SchoolModel,SchoolAdmin)
admin.site.register(models.StaffModel,StaffAdmin)
admin.site.register(models.Accounts,AccountsAdmin)
admin.site.register(models.ClassroomModel,ClassroomAdmin)
admin.site.register(models.BlackListedToken)
admin.site.register(models.Subject,SubjectAdmin)
admin.site.register(models.StudentModel,StudentAdmin)
admin.site.register(models.StudentAttendance,StudentAttendanceAdmin)
admin.site.register(models.StaffAttendance,StaffAttendanceAdmin)
admin.site.register(models.Notice)
admin.site.register(models.Attachment)
admin.site.register(models.SyllabusModel)
admin.site.register(models.ExamModel)
admin.site.register(models.ResultModel)
admin.site.register(models.TimeTableModel)
admin.site.register(models.CommonTimeModel)
admin.site.register(models.OTPModel)
admin.site.register(models.EventModel)
# Register your models here.
