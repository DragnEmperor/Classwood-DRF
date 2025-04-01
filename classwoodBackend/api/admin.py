from django.contrib import admin
from django.contrib.admin import ModelAdmin

from api import models


@admin.register(models.Accounts)
class AccountsAdmin(ModelAdmin):
    list_display = ("email", "id")


@admin.register(models.SchoolModel)
class SchoolAdmin(ModelAdmin):
    list_display = ("user", "school_name", "school_state")


@admin.register(models.SessionModel)
class SessionAdmin(ModelAdmin):
    list_display = ("start_date", "end_date", "is_active", "school")
    list_filter = ("is_active", "school")


@admin.register(models.StaffModel)
class StaffAdmin(ModelAdmin):
    list_display = ("user", "school", "first_name", "last_name")
    list_filter = ("school",)


@admin.register(models.StudentModel)
class StudentAdmin(ModelAdmin):
    list_display = ("full_name", "classroom", "school")
    list_filter = ("classroom", "school")


@admin.register(models.ClassroomModel)
class ClassroomAdmin(ModelAdmin):
    list_display = ("class_name", "section_name", "class_teacher", "school")
    list_filter = ("class_name", "school")


@admin.register(models.Subject)
class SubjectAdmin(ModelAdmin):
    list_display = ("name", "classroom", "teacher", "school")
    list_filter = ("classroom", "school")


@admin.register(models.StudentAttendance)
class StudentAttendanceAdmin(ModelAdmin):
    list_display = ("student", "date", "present")
    list_filter = ("date", "present")


@admin.register(models.StaffAttendance)
class StaffAttendanceAdmin(ModelAdmin):
    list_display = ("staff", "date", "present")
    list_filter = ("date", "present")


@admin.register(models.Notice)
class NoticeAdmin(ModelAdmin):
    list_display = ("title", "school", "session")
    list_filter = ("school", "session")


@admin.register(models.ExamModel)
class ExamAdmin(ModelAdmin):
    list_display = ("tag", "is_complete", "school", "session")
    list_filter = ("is_complete", "school", "session")


@admin.register(models.ResultModel)
class ResultAdmin(ModelAdmin):
    list_display = ("student", "exam", "session")
    list_filter = ("exam", "session")


@admin.register(models.SyllabusModel)
class SyllabusAdmin(ModelAdmin):
    list_display = ("subject", "classroom", "school", "session")
    list_filter = ("school", "session")


@admin.register(models.EventModel)
class EventAdmin(ModelAdmin):
    list_display = ("title", "school", "date", "session")
    list_filter = ("school", "session")


@admin.register(models.TimeTableModel)
class TimeTableAdmin(ModelAdmin):
    list_display = ("classroom", "school", "session")
    list_filter = ("school", "session")


@admin.register(models.CommonTimeModel)
class CommonTimeAdmin(ModelAdmin):
    list_display = ("classroom", "school", "session")
    list_filter = ("school", "session")


@admin.register(models.FeesDetails)
class FeesAdmin(ModelAdmin):
    list_display = ("for_class", "amount", "due_date", "school")
    list_filter = ("for_class", "school")


# Simple registrations (no custom admin)
admin.site.register(models.BlackListedToken)
admin.site.register(models.Attachment)
admin.site.register(models.OTPModel)
admin.site.register(models.ThoughtDayModel)
