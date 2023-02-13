from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,BaseUserManager,PermissionsMixin)
from uuid import uuid4
# Create your models here.
from .manager import CustomUserManager
from .validators import mobile_regex
from django.utils import timezone

def school_logo_upload(instance, filename):
    ext = filename.split(".")[-1]
    return f"schools/{instance.user.id}/logo_{uuid4().hex}.{ext}"

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
    
    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

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
    school_phone = models.CharField(validators=[mobile_regex], max_length=13)
    school_address = models.CharField(max_length=100)
    school_city = models.CharField(max_length=100)
    school_state = models.CharField(max_length=100)
    school_zipcode = models.CharField(max_length=100)
    school_logo = models.ImageField(upload_to=school_logo_upload, null=True, blank=True)
    school_website = models.URLField(max_length=200,null=True,blank=True)
    date_of_establishment = models.DateField(null=True,blank=True)
    staff_limit = models.CharField(max_length=10,default=25)
    student_limit = models.CharField(max_length=10,default=500)

    def __str__(self):
        return self.school_name
    
    def create(self, validated_data):
        return SchoolModel.objects.create(**validated_data)
    
    @property
    def staff_strength(self):
        return StaffModel.objects.all().count()
    
    @property
    def student_strength(self):
        return StudentModel.objects.all().count()
    
    # @property
    # def is_verified(self):
    #     return self.user.is_verified
    
    
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
    is_class_teacher = models.BooleanField(default=False)
    address = models.CharField(max_length=100)

    # School Information
    date_of_joining = models.DateField()

    class Meta:
        ordering = ["date_of_joining", "first_name", "last_name"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def incharge_of(self):
        return ClassroomModel.objects.get(class_teacher=self.user.id)
    
    @property
    def sub_incharge_of(self):
        return ClassroomModel.objects.filter(sub_class_teacher=self.user.id)

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
        unique_together = ("class_name", "section_name", "school")

    @property
    def strength(self):
        return StudentModel.objects.filter(className=self.id).count()

    def __str__(self):
        return f"{self.class_name} - {self.section_name}"
    

# add, if required, code for setting onDelete to models.SET() to class teacher
class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    subject_pic = models.ImageField(upload_to=subject_profile_upload, blank=True)
    teacher = models.ForeignKey(StaffModel, on_delete=models.SET_NULL, related_name="taught_by", null=True)
    classroom = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        unique_together = ("name","classroom")
        ordering = ["name"]

    def __str__(self):
        return self.name
    
    
class StudentModel(models.Model):
    GENDER_CHOICE = (("1", "Male"), ("2", "Female"), ("3", "Other"))

    user = models.OneToOneField(Accounts, on_delete=models.CASCADE, primary_key=True)
    profile_pic = models.ImageField(upload_to=student_profile_upload,null=True, blank=True)

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
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)

    # Class Information
    className = models.ForeignKey(
        ClassroomModel, on_delete=models.CASCADE, verbose_name="Class"
    )
    subjects = models.ManyToManyField(Subject, related_name="learning_subjects")
    

    def __str__(self):
        return self.roll_no

    class Meta:
        unique_together = ("school", "roll_no","admission_no","className")
        ordering = ["roll_no"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def get_attendance(self):
        att = Attendance.objects.filter(student=self.user.id).values("status")
        if not att:
            return 100
        return att.filter(status=True).count() / att.count() * 100
    
    @property
    def get_month_attendance(self):
        att_lst = [
            0 for _ in range(monthrange(timezone.now().year, timezone.now().month)[1])
        ]
        att = Attendance.objects.filter(
            student=self.user.id, date__gte=timezone.now().replace(day=1)
        )
        for i in att:
            att_lst[i.date.day - 1] = 2 if i.status else 1

        return json.dumps(att_lst)
    
class FeesDetails(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    due_date = models.DateField()
    description = models.TextField()
    for_class = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self):
        return f"{self.description} - {self.due_date}"


class PaymentInfo(models.Model):
    PAYMENT_MODE = (
        ("1", "Cheque"),
        ("2", "Cash at Counter"),
        ("3", "Net Banking"),
        ("4", "Demand Draft"),
    )

    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE)
    fees = models.ForeignKey(FeesDetails, on_delete=models.CASCADE)
    payment_mode = models.CharField(max_length=1, choices=PAYMENT_MODE)
    payment_date = models.DateField()
    reference = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.student.full_name

    class Meta:
        unique_together = ("student", "fees")
        ordering = ["-payment_date"]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

class Attendance(models.Model):
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance"
        indexes = [
            models.Index(fields=["student", "date"]),
        ]
        ordering = ["-date"]
        unique_together = ["student", "date"]

    @classmethod
    def get_attendance(cls, student):
        att = cls.objects.filter(student=student).values("status")
        if not att:
            return 100

        return att.filter(status=True).count() / att.count() * 100

    @classmethod
    def get_month_attendance(cls, student):
        att_lst = [
            0 for _ in range(monthrange(timezone.now().year, timezone.now().month)[1])
        ]
        att = cls.objects.filter(
            student=student, date__gte=timezone.now().replace(day=1)
        )
        for i in att:
            att_lst[i.date.day - 1] = 2 if i.status else 1

        return json.dumps(att_lst)

    def __str__(self):
        return self.student.user.email