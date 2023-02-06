from django.contrib import admin
from .models import Accounts,SchoolModel,StaffModel,ClassroomModel
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
        
admin.site.register(SchoolModel,SchoolAdmin)
admin.site.register(StaffModel,StaffAdmin)
admin.site.register(Accounts,AccountsAdmin)
admin.site.register(ClassroomModel,ClassroomAdmin)
# Register your models here.
