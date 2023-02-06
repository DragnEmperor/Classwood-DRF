from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,BaseUserManager,PermissionsMixin)
from uuid import uuid4
# Create your models here.
from .manager import CustomUserManager
from .validators import mobile_regex


def staff_profile_upload(instance, filename):
    ext = filename.split(".")[-1]
    return f"staff/{instance.user.id}/profile_{uuid4().hex}.{ext}"

def student_profile_upload(instance, filename):
    ext = filename.split(".")[-1]
    return f"students/{instance.user.id}/profile_{uuid4().hex}.{ext}"

def subject_profile_upload(instance, filename):
    ext = filename.split(".")[-1]
    return f"subjects/{instance.user.name}/profile_{uuid4().hex}.{ext}"



class Accounts(AbstractBaseUser, PermissionsMixin):
    """
    Accounts model
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField(unique=True,max_length=255)
    USERNAME_FIELD = "email"
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    objects = CustomUserManager()

class BlackListedToken(models.Model):
    token = models.CharField(max_length=500)
    user = models.ForeignKey(Accounts, related_name="token_user", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("token", "user")
        
        
class SchoolModel(models.Model):
    """
    SchoolSignUpModel model
    """
    user = models.OneToOneField(Accounts, on_delete=models.CASCADE,primary_key=True)
    school_name = models.CharField(max_length=100)
    school_phone = models.CharField(max_length=10)
    school_address = models.CharField(max_length=100)
    school_city = models.CharField(max_length=100)
    school_state = models.CharField(max_length=100)
    school_zipcode = models.CharField(max_length=100)
    school_logo = models.ImageField(upload_to='school_logo', null=True, blank=True)
    school_website = models.CharField(max_length=100)
    school_description = models.CharField(max_length=100,blank=True)

    def __str__(self):
        return self.school_name
    
    def create(self, validated_data):
        return SchoolModel.objects.create(**validated_data)
    
class StaffModel(models.Model):
    GENDER_CHOICE = (("1", "Male"), ("2", "Female"), ("3", "Other"))

    user = models.OneToOneField(Accounts, on_delete=models.CASCADE, primary_key=True)
    profile_pic = models.ImageField(upload_to=staff_profile_upload, blank=True)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)

    # Personal Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(auto_now_add=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICE)
    mobile_number = models.CharField(validators=[mobile_regex], max_length=13)
    contact_email = models.EmailField(null=True, blank=True)

    # School Information
    date_of_joining = models.DateField()

    class Meta:
        ordering = ["date_of_joining", "first_name", "last_name"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    # @property
    # def incharge(self):
    #     return ClassRecord.objects.filter(class_teacher=self)

    def __str__(self):
        return self.user.email
    
    
class ClassroomModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    # Class Information
    class_name = models.CharField(max_length=50)
    section_name = models.CharField(max_length=1)
    class_teacher = models.ForeignKey(StaffModel, on_delete=models.CASCADE)
    sub_class_teacher = models.ForeignKey(StaffModel, on_delete=models.CASCADE, related_name="sub_class_teacher", null=True, blank=True)

    # Subject Information
    # subjects = models.ManyToManyField(Subject, related_name="class_map")

    class Meta:
        ordering = ["class_name","section_name"]

    @property
    def strength(self):
        return StudentInfo.objects.filter(class_id=self).count()

    def __str__(self):
        return f"{self.class_name} - {self.section_name}"
    

class StudentModel(models.Model):
    GENDER_CHOICE = (("1", "Male"), ("2", "Female"), ("3", "Other"))

    user = models.OneToOneField(Accounts, on_delete=models.CASCADE, primary_key=True)
    profile_pic = models.ImageField(upload_to=student_profile_upload, blank=True)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)

    # Personal Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICE)
    address = models.TextField(max_length=200)
    contact_email = models.EmailField(null=True, blank=True)

    # Parent Information
    father_name = models.CharField(max_length=50)
    mother_name = models.CharField(max_length=50)
    parent_mobile_number = models.CharField(
        validators=[mobile_regex], max_length=13, blank=True
    )

    # School Information
    date_of_admission = models.DateField()
    roll_no = models.CharField(max_length=20)
    admission_no = models.CharField(max_length=35)

    # Class Information
    className = models.ForeignKey(
        ClassroomModel, on_delete=models.CASCADE, verbose_name="Class"
    )

    def __str__(self):
        return self.user.roll_no

    class Meta:
        unique_together = ("school", "roll_no")
        ordering = ["roll_no"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.user.email

class Subject(models.Model):
    name = models.CharField(max_length=50)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(null=True, auto_now_add=True)
    classroom = models.ManyToManyField(ClassroomModel, related_name="class_map")
    subject_pic = models.ImageField(upload_to=subject_profile_upload, blank=True)

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        unique_together = ("name", "school")
        ordering = ["name"]

    def __str__(self):
        return self.name