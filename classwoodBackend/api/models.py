from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,BaseUserManager,PermissionsMixin)
from uuid import uuid4
from .manager import CustomUserManager
from .validators import mobile_regex
from django.utils import timezone
from django.conf import settings
from calendar import monthrange
import json,os,datetime
from rest_framework import serializers

def school_logo_upload(instance, filename):
    ext = filename.split(".")[-1]
    newName = instance.school_name.split(' ')
    newName = '_'.join(newName)
    generated_name = f"schools/{newName}/logo_{uuid4().hex}.{ext}"
    instance.school_logo_url = f'{settings.MEDIA_URL}{generated_name}'
    return generated_name

def staff_profile_upload(instance, filename):
    ext = filename.split(".")[-1]
    newName = instance.last_name.split(' ')
    newName = '_'.join(newName)
    generated_name = f"schools/{instance.school.school_name}/staff/{instance.first_name}_{newName}/pic_{uuid4().hex}.{ext}"
    instance.profile_pic_url = f'{settings.MEDIA_URL}{generated_name}'
    return generated_name

def student_profile_upload(instance, filename):
    ext = filename.split(".")[-1]
    newName = instance.last_name.split(' ')
    newName = '_'.join(newName)
    generated_name = f"schools/{instance.school.school_name}/students/{instance.first_name}_{newName}/pic_{uuid4().hex}.{ext}"
    instance.profile_pic_url = f'{settings.MEDIA_URL}{generated_name}'
    return generated_name

def subject_profile_upload(instance, filename):
    ext = filename.split(".")[-1]
    newName = str(instance.classroom)
    generated_name = f"schools/{instance.school.school_name}/subjects/{newName}/pic_{uuid4().hex}.{ext}"
    instance.subject_pic_url = f'{settings.MEDIA_URL}{generated_name}'
    return generated_name

def notice_attach_upload(instance, filename):
    ext = filename.split(".")[-1]
    file_title = os.path.splitext(filename)[0]
    generated_name = f"schools/{instance.school.school_name}/{instance.attachType}/{file_title}_{uuid4().hex}.{ext}"
    return generated_name


class YearAttendanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    present = serializers.BooleanField()
        
# ACCOUNTS, AUTH RELATED MODELS
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

# SCHOOL SIGNUP RELATED MODELS
class SchoolModel(models.Model):
    """
    SchoolSignUpModel model
    """

    BOARD_CHOICE = (("ICSE", "ICSE"), ("CBSE", "CBSE"), ("HPBOSE", "HPBOSE"))
    user = models.OneToOneField(Accounts, on_delete=models.CASCADE,primary_key=True)
    school_name = models.CharField(max_length=100)
    school_phone = models.CharField(validators=[mobile_regex], max_length=13)
    school_address = models.CharField(max_length=100)
    school_city = models.CharField(max_length=100)
    school_state = models.CharField(max_length=100)
    school_zipcode = models.CharField(max_length=100)
    school_logo = models.ImageField(upload_to=school_logo_upload, null=True, blank=True)
    school_logo_url = models.CharField(max_length=500, null=True, blank=True)
    school_website = models.URLField(max_length=200,null=True,blank=True)
    date_of_establishment = models.DateField(null=True,blank=True)
    staff_limit = models.CharField(max_length=10,default=25)
    student_limit = models.CharField(max_length=10,default=500)
    school_board = models.CharField(max_length=7,choices=BOARD_CHOICE, default="CBSE")
    school_affNo = models.CharField(max_length=30, default="1")
    school_head = models.CharField(max_length=30,null=True,blank=True)


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

class SessionModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    start_date = models.DateField()
    end_date = models.DateField(null=True,blank=True)
    is_active = models.BooleanField(default=False)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)

    @property
    def deactivate_if_expired(self):
        if self.end_date and self.end_date == self.start_date:
            self.is_active = False
            self.save()


class StaffModel(models.Model):
    GENDER_CHOICE = (("1", "Male"), ("2", "Female"), ("3", "Other"))

    user = models.OneToOneField(Accounts, on_delete=models.CASCADE, primary_key=True)
    profile_pic = models.ImageField(upload_to=staff_profile_upload, blank=True)
    profile_pic_url = models.CharField(max_length=500, null=True, blank=True)

    # Personal Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICE)
    mobile_number = models.CharField(validators=[mobile_regex], max_length=13)
    contact_email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=100)
    account_no = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=50, default="12345678")
    is_teaching_staff = models.BooleanField(default=True)

    # School Information
    is_class_teacher = models.BooleanField(default=False)
    date_of_joining = models.DateField()
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ["date_of_joining", "first_name", "last_name"]
        unique_together = ("first_name","last_name","mobile_number", "school", "session")

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

    @property
    def get_gender_display(self):
        for choice in self.GENDER_CHOICE:
            if choice[0] == self.gender:
                return choice[1]
        return None

    @property
    def get_attendance(self):
        att = StaffAttendance.objects.filter(staff=self.user.id).values("present")
        if not att:
            return 100
        return att.filter(present=True).count() / att.count() * 100

    @property
    def get_month_attendance(self):
        att_lst = [
            0 for _ in range(monthrange(timezone.now().year, timezone.now().month)[1])
        ]
        att = StaffAttendance.objects.filter(
            staff=self.user.id, date__gte=timezone.now().replace(day=1)
        )
        for i in att:
            att_lst[i.date.day - 1] = 2 if i.present else 1

        return json.dumps(att_lst)
    
    @property
    def get_year_attendance(self):
       year = timezone.now().year
       att_lst = []
       for month in range(1, 13):
          days_in_month = monthrange(year, month)[1]
          month_attendance = [
            {'date': datetime.date(year, month, day).strftime('%Y-%m-%d'), 'present': False}
            for day in range(1, days_in_month+1)
          ]
          att = StaffAttendance.objects.filter(
            staff=self.user.id,
            date__year=year,
            date__month=month
          )
          serializer = YearAttendanceSerializer(att, many=True)
          for i in serializer.data:
            day = int(i['date'].split('-')[2])
            month_attendance[day-1]['present'] = i['present']
          att_lst.append({'month': month, 'attendance_records': month_attendance})
       return att_lst
    
    

# CLASSROOM RELATED MODELS
class ClassroomModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    # Class Information
    class_name = models.CharField(max_length=50)
    section_name = models.CharField(max_length=20)
    class_teacher = models.ForeignKey(StaffModel, on_delete=models.SET_NULL,null=True)
    sub_class_teacher = models.ForeignKey(StaffModel, on_delete=models.SET_NULL, related_name="sub_class_teacher", null=True, blank=True)
    teachers = models.ManyToManyField(StaffModel,related_name='teachers_of_class',blank=True)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)
    # Subject Information
    # subjects = models.ManyToManyField(Subject, related_name="class_map")

    class Meta:
        ordering = ["class_name","section_name"]
        unique_together = ("class_name", "section_name", "school", "session")

    @property
    def strength(self):
        return StudentModel.objects.filter(classroom=self.id).count()

    def __str__(self):
        return f"{self.class_name}-{self.section_name}"

    @property
    def no_of_subjects(self):
        return Subject.objects.filter(classroom=self.id).count()

    @property
    def no_of_teachers(self):
        return  self.teachers.all().count()


# add, if required, code for setting onDelete to models.SET() to class teacher
class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    subject_pic = models.ImageField(upload_to=subject_profile_upload, blank=True)
    subject_pic_url = models.CharField(max_length=500, null=True, blank=True)
    teacher = models.ForeignKey(StaffModel, on_delete=models.SET_NULL, related_name="taught_by", null=True)
    classroom = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        unique_together = ("name","classroom","session")
        ordering = ["name"]

    def __str__(self):
        return f'{self.name}'


class StudentModel(models.Model):
    GENDER_CHOICE = (("1", "Male"), ("2", "Female"), ("3", "Other"))

    user = models.OneToOneField(Accounts, on_delete=models.CASCADE, primary_key=True)
    profile_pic = models.ImageField(upload_to=student_profile_upload,null=True, blank=True)
    profile_pic_url = models.CharField(max_length=500, null=True, blank=True)

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
    parent_account_no = models.CharField(max_length=100,null=True,blank=True)

    # School Information
    date_of_admission = models.DateField()
    roll_no = models.CharField(max_length=20)
    admission_no = models.CharField(max_length=35)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)
    waiver_percent = models.DecimalField(decimal_places=5,max_digits=10,default=0)
    waiver_type = models.CharField(max_length=30,default='none')

    # Class Information
    classroom = models.ForeignKey(
        ClassroomModel, on_delete=models.SET_NULL, verbose_name="Class",null=True
    )
    subjects = models.ManyToManyField(Subject, related_name="learning_subjects", blank=True)


    def __str__(self):
        return self.roll_no

    class Meta:
        unique_together = ("school", "roll_no","admission_no","classroom","session")
        ordering = ["roll_no"]

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def get_attendance(self):
        att = StudentAttendance.objects.filter(student=self.user.id).values("present")
        if not att:
            return 100
        return att.filter(present=True).count() / att.count() * 100

    @property
    def get_month_attendance(self):
        att_lst = [
            0 for _ in range(monthrange(timezone.now().year, timezone.now().month)[1])
        ]
        att = StudentAttendance.objects.filter(
            student=self.user.id, date__gte=timezone.now().replace(day=1)
        )
        for i in att:
            att_lst[i.date.day - 1] = 2 if i.present else 1

        return json.dumps(att_lst)
    
    @property
    def get_year_attendance(self):
       year = timezone.now().year
       att_lst = []
       for month in range(1, 13):
          days_in_month = monthrange(year, month)[1]
          month_attendance = [
            {'date': datetime.date(year, month, day).strftime('%Y-%m-%d'), 'present': False}
            for day in range(1, days_in_month+1)
          ]
          att = StudentAttendance.objects.filter(
            student=self.user.id,
            date__year=year,
            date__month=month
          )
          serializer = YearAttendanceSerializer(att, many=True)
          for i in serializer.data:
            day = int(i['date'].split('-')[2])
            month_attendance[day-1]['present'] = i['present']
          att_lst.append({'month': month, 'attendance_records': month_attendance})
       return att_lst

    @property
    def get_gender_display(self):
        for choice in self.GENDER_CHOICE:
            if choice[0] == self.gender:
                return choice[1]
        return None

# ATTENDANCE RELATED MODEL
class StudentYearAttendance(models.Model):
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE)
    year = models.IntegerField()
    attendance_data = models.JSONField()

    class Meta:
        verbose_name = "StudentYearAttendance"
        verbose_name_plural = "StudentYearAttendance"
        indexes = [
            models.Index(fields=["student", "year"]),
        ]
        unique_together = ["student", "year"]

    def __str__(self):
        return f"{self.student.user.email} ({self.year})"
    
    
class StaffYearAttendance(models.Model):
    staff = models.ForeignKey(StaffModel, on_delete=models.CASCADE)
    year = models.IntegerField()
    attendance_data = models.JSONField()

    class Meta:
        verbose_name = "StaffYearAttendance"
        verbose_name_plural = "StaffYearAttendance"
        indexes = [
            models.Index(fields=["staff", "year"]),
        ]
        unique_together = ["staff", "year"]

    def __str__(self):
        return f"{self.staff.user.email} ({self.year})"
    
    
class StudentAttendance(models.Model):
    student = models.ForeignKey(StudentModel, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    present = models.BooleanField(default=False)
    classroom = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "StudentAttendance"
        verbose_name_plural = "StudentAttendance"
        indexes = [
            models.Index(fields=["student", "date"]),
        ]
        ordering = ["-date"]
        unique_together = ["student", "date",]

    def __str__(self):
        return self.student.user.email
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        year = self.date.year
        try:
            year_attendance = StudentYearAttendance.objects.get(
                student=self.student,
                year=year
            )
        except StudentYearAttendance.DoesNotExist:
            year_attendance = StudentYearAttendance(
                student=self.student,
                year=year,
                attendance_data=[]
            )
        year_attendance.attendance_data = json.loads(self.student.get_year_attendance)
        year_attendance.save()

class StaffAttendance(models.Model):
    staff = models.ForeignKey(StaffModel, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    present = models.BooleanField(default=False)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "StaffAttendance"
        verbose_name_plural = "StaffAttendance"
        indexes = [
            models.Index(fields=["staff", "date"]),
        ]
        ordering = ["-date"]
        unique_together = ["staff", "date"]

    def __str__(self):
        return self.student.user.email
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        year = self.date.year
        try:
            year_attendance = StaffYearAttendance.objects.get(
                staff=self.staff,
                year=year
            )
        except StaffYearAttendance.DoesNotExist:
            year_attendance = StaffYearAttendance(
                staff=self.staff,
                year=year,
                attendance_data=[]
            )
        year_attendance.attendance_data = json.loads(self.staff.get_year_attendance)
        year_attendance.save()

# NOTICE RELATED MODELS
class Notice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    attachments = models.ManyToManyField('Attachment',blank=True)
    read_by_students = models.ManyToManyField('StudentModel', related_name="read_by_students", blank=True)
    read_by_staff = models.ManyToManyField('StaffModel', related_name="read_by_teachers", blank=True)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date_posted"]
        unique_together = ("school", "title",'date_posted')

    @classmethod
    def read_status(cls,notice,currentUser):
        return notice.read_by_students.filter(id=currentUser).exists() | notice.read_by_staff.filter(id=currentUser).exists()

    def __str__(self):
        return self.title

class Attachment(models.Model):
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)
    attachType = models.CharField(max_length=50, null=True, blank=True)
    fileName = models.FileField(upload_to=notice_attach_upload, null=True, blank=True)

    def __str__(self):
        return self.fileName.url


#PAYMENT RELATED MODELS
class FeesDetails(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    due_date = models.DateField(null=True,blank=True)
    description = models.TextField(null=True,blank=True)
    for_class = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)
    fee_type = models.TextField()
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-due_date"]

    def __str__(self):
        return f"{self.fee_type} - {self.amount}"

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

# EXAM RELATED MODELS
class ExamModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    # Exam Information
    tag = models.CharField(max_length=50)
    classroom = models.ForeignKey("ClassroomModel", on_delete=models.CASCADE)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    max_marks = models.IntegerField(default=100)
    attachments = models.ManyToManyField('Attachment',blank=True)
    description = models.CharField(max_length=200,null=True,blank=True)
    date_of_exam = models.DateField()
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_of_exam"]
        unique_together = ("school", "classroom", "subject","date_of_exam")

    def __str__(self):
        return self.tag

class ResultModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    student = models.ForeignKey("StudentModel", on_delete=models.CASCADE)
    exam = models.ForeignKey("ExamModel", on_delete=models.CASCADE)
    score = models.IntegerField()
    attachments = models.ManyToManyField('Attachment',blank=True)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-exam__date_of_exam"]
        unique_together = ["student", "exam","session"]

    def __str__(self):
        return self.student.full_name


class SyllabusModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    classroom = models.ForeignKey("ClassroomModel", on_delete=models.CASCADE)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    attachments = models.ManyToManyField('Attachment',blank=True)
    tag = models.CharField(max_length=50,blank=True,null=True)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)

    class Meta:
        # ordering = ["-date_of_exam"]
        unique_together = ("school", "classroom", "subject","session")

    def __str__(self):
        return f"{self.subject.name}_{self.tag}"

class EventModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    attachments = models.ManyToManyField('Attachment',blank=True)
    # tag = models.CharField(max_length=50,blank=True,null=True)
    date = models.DateField()
    title = models.CharField(max_length=50)
    description = models.TextField()
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("school", "date","title",)


class TimeTableModel(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    DAYS_OF_WEEK = (
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        # ('Sunday', 'Sunday')
    )
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    classroom = models.ForeignKey('ClassroomModel', related_name='timetables', on_delete=models.CASCADE)
    day = models.CharField(choices=DAYS_OF_WEEK, max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey('StaffModel', on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)


class CommonTimeModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    classroom = models.ForeignKey('ClassroomModel', related_name='commontime', on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.CharField(max_length=128)
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)

class OTPModel(models.Model):
    email = models.EmailField()
    hashed_otp = models.CharField(max_length=128)
    expiration_time = models.DateTimeField()

class ThoughtDayModel(models.Model):
    content = models.TextField()
    date = models.DateField()
    session = models.ForeignKey(SessionModel, on_delete=models.CASCADE)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)

