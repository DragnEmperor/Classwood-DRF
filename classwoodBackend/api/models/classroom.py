from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint


def subject_profile_upload(instance, filename):
    ext = filename.rsplit(".", 1)[-1]
    label = str(instance.classroom)
    school_name = instance.school.school_name
    generated_name = f"schools/{school_name}/subjects/{label}/pic_{uuid4().hex}.{ext}"
    instance.subject_pic_url = f"{settings.MEDIA_URL}{generated_name}"
    return generated_name


class ClassroomModel(models.Model):
    """Represents a class section (e.g. 10-A)."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    class_name = models.CharField(max_length=50)
    section_name = models.CharField(max_length=20)
    class_teacher = models.ForeignKey("StaffModel", on_delete=models.SET_NULL, null=True)
    sub_class_teacher = models.ForeignKey(
        "StaffModel", on_delete=models.SET_NULL, related_name="sub_class_teacher", null=True, blank=True
    )
    teachers = models.ManyToManyField("StaffModel", related_name="teachers_of_class", blank=True)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    class Meta:
        ordering = ["class_name", "section_name"]
        constraints = [
            UniqueConstraint(
                fields=["class_name", "section_name", "school", "session"],
                name="unique_classroom_per_school_session",
            ),
        ]

    def __str__(self):
        return f"{self.class_name}-{self.section_name}"

    @property
    def strength(self):
        from api.models.student import StudentModel

        return StudentModel.objects.filter(classroom=self).count()

    @property
    def no_of_subjects(self):
        return Subject.objects.filter(classroom=self).count()

    @property
    def no_of_teachers(self):
        return self.teachers.count()


class Subject(models.Model):
    """A subject taught in a classroom."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    subject_pic = models.ImageField(upload_to=subject_profile_upload, blank=True)
    subject_pic_url = models.CharField(max_length=500, null=True, blank=True)
    teacher = models.ForeignKey("StaffModel", on_delete=models.SET_NULL, related_name="taught_by", null=True)
    classroom = models.ForeignKey(ClassroomModel, on_delete=models.CASCADE)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        constraints = [
            UniqueConstraint(
                fields=["name", "classroom", "session"],
                name="unique_subject_per_classroom_session",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name
