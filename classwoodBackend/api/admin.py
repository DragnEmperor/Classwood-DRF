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
    
class SessionAdmin(ModelAdmin):
    list_display = ("start_date","end_date","is_active","school")
    list_filter = ("start_date","is_active","school")
    
class SyllabusAdmin(ModelAdmin):
    list_display = ("subject","classroom","school","session")
    list_filter = ("subject","classroom","school","session")

class ResultAdmin(ModelAdmin):
    list_display = ("student","exam","session")
    list_filter = ("student","exam","session")

class NoticeAdmin(ModelAdmin):
    list_display = ("title","school","session")
    list_filter = ("title","school","session")

class ExamAdmin(ModelAdmin):
    list_display = ("tag","is_complete","school","session")
    list_filter = ("tag","is_complete","school","session")
    
class EventAdmin(ModelAdmin):
    list_display = ("title","school","date","session")
    list_filter = ("title","school","session")
    
class FeesAdmin(ModelAdmin):
    list_display = ("for_class","amount","due_date","school")
    list_filter = ("for_class","session","school",)
        
admin.site.register(models.SchoolModel,SchoolAdmin)
admin.site.register(models.StaffModel,StaffAdmin)
admin.site.register(models.Accounts,AccountsAdmin)
admin.site.register(models.ClassroomModel,ClassroomAdmin)
admin.site.register(models.BlackListedToken)
admin.site.register(models.Subject,SubjectAdmin)
admin.site.register(models.StudentModel,StudentAdmin)
admin.site.register(models.StudentAttendance,StudentAttendanceAdmin)
admin.site.register(models.StaffAttendance,StaffAttendanceAdmin)
admin.site.register(models.Notice,NoticeAdmin)
admin.site.register(models.Attachment)
admin.site.register(models.SyllabusModel,SyllabusAdmin)
admin.site.register(models.ExamModel,ExamAdmin)
admin.site.register(models.ResultModel,ResultAdmin)
admin.site.register(models.TimeTableModel)
admin.site.register(models.CommonTimeModel)
admin.site.register(models.OTPModel)
admin.site.register(models.EventModel,EventAdmin)
admin.site.register(models.SessionModel,SessionAdmin)
admin.site.register(models.ThoughtDayModel)
admin.site.register(models.FeesDetails,FeesAdmin)
# Register your models here.
