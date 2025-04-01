import datetime

from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone


class StudentAttendance(models.Model):
    """Daily attendance record for a student."""

    student = models.ForeignKey("StudentModel", on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    present = models.BooleanField(default=False)
    classroom = models.ForeignKey("ClassroomModel", on_delete=models.CASCADE)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "StudentAttendance"
        verbose_name_plural = "StudentAttendance"
        indexes = [models.Index(fields=["student", "date"])]
        ordering = ["-date"]
        constraints = [
            UniqueConstraint(fields=["student", "date"], name="unique_student_attendance_per_date"),
        ]

    def __str__(self):
        return f"{self.student} - {self.date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_year_attendance()

    def _update_year_attendance(self):
        year = self.date.year
        obj, _ = StudentYearAttendance.objects.get_or_create(
            student=self.student,
            year=year,
            defaults={"attendance_data": []},
        )
        obj.attendance_data = self.student.year_attendance
        obj.save(update_fields=["attendance_data"])


class StaffAttendance(models.Model):
    """Daily attendance record for a staff member."""

    staff = models.ForeignKey("StaffModel", on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    present = models.BooleanField(default=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "StaffAttendance"
        verbose_name_plural = "StaffAttendance"
        indexes = [models.Index(fields=["staff", "date"])]
        ordering = ["-date"]
        constraints = [
            UniqueConstraint(fields=["staff", "date"], name="unique_staff_attendance_per_date"),
        ]

    def __str__(self):
        return f"{self.staff} - {self.date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_year_attendance()

    def _update_year_attendance(self):
        year = self.date.year
        obj, _ = StaffYearAttendance.objects.get_or_create(
            staff=self.staff,
            year=year,
            defaults={"attendance_data": []},
        )
        obj.attendance_data = self.staff.year_attendance
        obj.save(update_fields=["attendance_data"])


class StudentYearAttendance(models.Model):
    """Cached yearly attendance snapshot for a student."""

    student = models.ForeignKey("StudentModel", on_delete=models.CASCADE)
    year = models.IntegerField()
    attendance_data = models.JSONField()

    class Meta:
        verbose_name = "StudentYearAttendance"
        verbose_name_plural = "StudentYearAttendance"
        indexes = [models.Index(fields=["student", "year"])]
        constraints = [
            UniqueConstraint(fields=["student", "year"], name="unique_student_year_attendance"),
        ]

    def __str__(self):
        return f"{self.student} ({self.year})"


class StaffYearAttendance(models.Model):
    """Cached yearly attendance snapshot for a staff member."""

    staff = models.ForeignKey("StaffModel", on_delete=models.CASCADE)
    year = models.IntegerField()
    attendance_data = models.JSONField()

    class Meta:
        verbose_name = "StaffYearAttendance"
        verbose_name_plural = "StaffYearAttendance"
        indexes = [models.Index(fields=["staff", "year"])]
        constraints = [
            UniqueConstraint(fields=["staff", "year"], name="unique_staff_year_attendance"),
        ]

    def __str__(self):
        return f"{self.staff} ({self.year})"
