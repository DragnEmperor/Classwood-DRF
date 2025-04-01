import datetime
from calendar import monthrange
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone

from api.validators import mobile_regex


def staff_profile_upload(instance, filename):
    ext = filename.rsplit(".", 1)[-1]
    slug = instance.last_name.replace(" ", "_")
    school_name = instance.school.school_name
    generated_name = f"schools/{school_name}/staff/{instance.first_name}_{slug}/pic_{uuid4().hex}.{ext}"
    instance.profile_pic_url = f"{settings.MEDIA_URL}{generated_name}"
    return generated_name


class StaffModel(models.Model):
    """Represents a staff member (teacher or non-teaching)."""

    GENDER_CHOICES = [("1", "Male"), ("2", "Female"), ("3", "Other")]

    user = models.OneToOneField("Accounts", on_delete=models.CASCADE, primary_key=True)
    profile_pic = models.ImageField(upload_to=staff_profile_upload, blank=True)
    profile_pic_url = models.CharField(max_length=500, null=True, blank=True)

    # Personal
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    mobile_number = models.CharField(validators=[mobile_regex], max_length=13)
    contact_email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=100)
    account_no = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=50, default="12345678")
    is_teaching_staff = models.BooleanField(default=True)

    # School
    is_class_teacher = models.BooleanField(default=False)
    date_of_joining = models.DateField()
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ["date_of_joining", "first_name", "last_name"]
        constraints = [
            UniqueConstraint(
                fields=["first_name", "last_name", "mobile_number", "school", "session"],
                name="unique_staff_per_school_session",
            ),
        ]

    def __str__(self):
        return self.user.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def gender_display(self):
        return dict(self.GENDER_CHOICES).get(self.gender)

    @property
    def incharge_of(self):
        from api.models.classroom import ClassroomModel

        return ClassroomModel.objects.filter(class_teacher=self.user_id).first()

    @property
    def sub_incharge_of(self):
        from api.models.classroom import ClassroomModel

        return ClassroomModel.objects.filter(sub_class_teacher=self.user_id)

    @property
    def total_attendance(self):
        from api.models.attendance import StaffAttendance

        qs = StaffAttendance.objects.filter(staff=self.user_id)
        total = qs.count()
        if not total:
            return 100
        return qs.filter(present=True).count() / total * 100

    @property
    def month_attendance(self):
        from api.models.attendance import StaffAttendance

        now = timezone.now()
        days_in_month = monthrange(now.year, now.month)[1]
        att_list = [0] * days_in_month

        records = StaffAttendance.objects.filter(
            staff=self.user_id,
            date__gte=now.replace(day=1),
        ).values("date", "present")

        for record in records:
            att_list[record["date"].day - 1] = 2 if record["present"] else 1

        return att_list

    @property
    def year_attendance(self):
        from api.models.attendance import StaffAttendance

        year = timezone.now().year
        result = []

        for month in range(1, 13):
            days = monthrange(year, month)[1]
            month_data = [
                {"date": datetime.date(year, month, day).isoformat(), "present": False} for day in range(1, days + 1)
            ]

            records = StaffAttendance.objects.filter(
                staff=self.user_id,
                date__year=year,
                date__month=month,
            ).values("date", "present")

            for record in records:
                day_idx = record["date"].day - 1
                month_data[day_idx]["present"] = record["present"]

            result.append({"month": month, "attendance_records": month_data})

        return result
