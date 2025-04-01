import datetime
from calendar import monthrange
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone

from api.validators import mobile_regex


def student_profile_upload(instance, filename):
    ext = filename.rsplit(".", 1)[-1]
    slug = instance.last_name.replace(" ", "_")
    school_name = instance.school.school_name
    generated_name = f"schools/{school_name}/students/{instance.first_name}_{slug}/pic_{uuid4().hex}.{ext}"
    instance.profile_pic_url = f"{settings.MEDIA_URL}{generated_name}"
    return generated_name


class StudentModel(models.Model):
    """Represents a student enrolled in a school."""

    GENDER_CHOICES = [("1", "Male"), ("2", "Female"), ("3", "Other")]

    user = models.OneToOneField("Accounts", on_delete=models.CASCADE, primary_key=True)
    profile_pic = models.ImageField(upload_to=student_profile_upload, null=True, blank=True)
    profile_pic_url = models.CharField(max_length=500, null=True, blank=True)

    # Personal
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField(max_length=200)
    contact_email = models.EmailField(null=True, blank=True)

    # Parent
    father_name = models.CharField(max_length=50)
    mother_name = models.CharField(max_length=50)
    parent_mobile_number = models.CharField(validators=[mobile_regex], max_length=13, blank=True)
    parent_account_no = models.CharField(max_length=100, null=True, blank=True)

    # School
    date_of_admission = models.DateField()
    roll_no = models.CharField(max_length=20)
    admission_no = models.CharField(max_length=35)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)
    waiver_percent = models.DecimalField(decimal_places=5, max_digits=10, default=0)
    waiver_type = models.CharField(max_length=30, default="none")

    # Class
    classroom = models.ForeignKey("ClassroomModel", on_delete=models.SET_NULL, verbose_name="Class", null=True)
    subjects = models.ManyToManyField("Subject", related_name="learning_subjects", blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["school", "roll_no", "admission_no", "classroom", "session"],
                name="unique_student_per_school_session",
            ),
        ]
        ordering = ["roll_no"]

    def __str__(self):
        return self.roll_no

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def gender_display(self):
        return dict(self.GENDER_CHOICES).get(self.gender)

    @property
    def total_attendance(self):
        records = self._attendance_records()
        if records is None:
            from api.models.attendance import StudentAttendance

            qs = StudentAttendance.objects.filter(student=self.user_id)
            total = qs.count()
            return 100 if not total else qs.filter(present=True).count() / total * 100

        if not records:
            return 100
        present = sum(1 for r in records if r.present)
        return present / len(records) * 100

    @property
    def month_attendance(self):
        now = timezone.now()
        days_in_month = monthrange(now.year, now.month)[1]
        att_list = [0] * days_in_month
        first_of_month = now.replace(day=1).date()

        records = self._attendance_records()
        if records is None:
            from api.models.attendance import StudentAttendance

            records = StudentAttendance.objects.filter(
                student=self.user_id, date__gte=first_of_month
            ).values("date", "present")
            for record in records:
                att_list[record["date"].day - 1] = 2 if record["present"] else 1
            return att_list

        for record in records:
            if record.date >= first_of_month and record.date.month == now.month and record.date.year == now.year:
                att_list[record.date.day - 1] = 2 if record.present else 1
        return att_list

    @property
    def year_attendance(self):
        year = timezone.now().year
        records = self._attendance_records()
        result = []

        if records is None:
            from api.models.attendance import StudentAttendance

            records = list(
                StudentAttendance.objects.filter(student=self.user_id, date__year=year).values("date", "present")
            )
            records_by_month = {}
            for r in records:
                records_by_month.setdefault(r["date"].month, []).append(r)

            for month in range(1, 13):
                days = monthrange(year, month)[1]
                month_data = [
                    {"date": datetime.date(year, month, day).isoformat(), "present": False}
                    for day in range(1, days + 1)
                ]
                for r in records_by_month.get(month, []):
                    month_data[r["date"].day - 1]["present"] = r["present"]
                result.append({"month": month, "attendance_records": month_data})
            return result

        records_by_month = {}
        for r in records:
            if r.date.year == year:
                records_by_month.setdefault(r.date.month, []).append(r)

        for month in range(1, 13):
            days = monthrange(year, month)[1]
            month_data = [
                {"date": datetime.date(year, month, day).isoformat(), "present": False}
                for day in range(1, days + 1)
            ]
            for r in records_by_month.get(month, []):
                month_data[r.date.day - 1]["present"] = r.present
            result.append({"month": month, "attendance_records": month_data})
        return result

    def _attendance_records(self):
        """
        Returns prefetched StudentAttendance records if the queryset used
        `prefetch_related("studentattendance_set")`, else None.
        """
        cache = getattr(self, "_prefetched_objects_cache", None) or {}
        records = cache.get("studentattendance_set")
        return list(records) if records is not None else None
