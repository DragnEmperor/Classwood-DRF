from uuid import uuid4

from django.conf import settings
from django.db import models

from api.validators import mobile_regex


def school_logo_upload(instance, filename):
    ext = filename.rsplit(".", 1)[-1]
    slug = instance.school_name.replace(" ", "_")
    generated_name = f"schools/{slug}/logo_{uuid4().hex}.{ext}"
    instance.school_logo_url = f"{settings.MEDIA_URL}{generated_name}"
    return generated_name


class SchoolModel(models.Model):
    """Represents a registered school."""

    BOARD_CHOICES = [
        ("ICSE", "ICSE"),
        ("CBSE", "CBSE"),
        ("HPBOSE", "HPBOSE"),
    ]

    user = models.OneToOneField("Accounts", on_delete=models.CASCADE, primary_key=True)
    school_name = models.CharField(max_length=100)
    school_phone = models.CharField(validators=[mobile_regex], max_length=13)
    school_address = models.CharField(max_length=100)
    school_city = models.CharField(max_length=100)
    school_state = models.CharField(max_length=100)
    school_zipcode = models.CharField(max_length=100)
    school_logo = models.ImageField(upload_to=school_logo_upload, null=True, blank=True)
    school_logo_url = models.CharField(max_length=500, null=True, blank=True)
    school_website = models.URLField(max_length=200, null=True, blank=True)
    date_of_establishment = models.DateField(null=True, blank=True)
    staff_limit = models.CharField(max_length=10, default="25")
    student_limit = models.CharField(max_length=10, default="500")
    school_board = models.CharField(max_length=7, choices=BOARD_CHOICES, default="CBSE")
    school_affNo = models.CharField(max_length=30, default="1")
    school_head = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        verbose_name = "School"
        verbose_name_plural = "Schools"

    def __str__(self):
        return self.school_name

    @property
    def staff_strength(self):
        from api.models.staff import StaffModel

        return StaffModel.objects.filter(school=self).count()

    @property
    def student_strength(self):
        from api.models.student import StudentModel

        return StudentModel.objects.filter(school=self).count()


class SessionModel(models.Model):
    """Academic session with start/end dates."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    school = models.ForeignKey(SchoolModel, on_delete=models.CASCADE)

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.start_date} - {self.end_date or '...'} ({status})"

    def deactivate_if_expired(self):
        if self.end_date and self.end_date <= self.start_date:
            self.is_active = False
            self.save(update_fields=["is_active"])
