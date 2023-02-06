from uuid import uuid4

from django.db import models

from apps.accounts.models import StudentInfo

from .subject import Subject


class ClassRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("api.SchoolModel", on_delete=models.CASCADE)
    # Class Information
    class_name = models.CharField(max_length=50)
    class_teacher = models.ForeignKey("api.StaffModel", on_delete=models.CASCADE)

    # Subject Information
    # subjects = models.ManyToManyField(Subject, related_name="class_map")

    class Meta:
        ordering = ["class_name"]

    @property
    def strength(self):
        return StudentInfo.objects.filter(class_id=self).count()

    def __str__(self):
        return self.class_name
