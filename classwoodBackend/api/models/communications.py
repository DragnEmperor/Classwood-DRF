import os
from uuid import uuid4

from django.db import models
from django.db.models import UniqueConstraint
from django.utils import timezone


def notice_attach_upload(instance, filename):
    ext = filename.rsplit(".", 1)[-1]
    file_title = os.path.splitext(filename)[0]
    school_name = instance.school.school_name
    generated_name = f"schools/{school_name}/{instance.attachType}/{file_title}_{uuid4().hex}.{ext}"
    return generated_name


class Attachment(models.Model):
    """File attachment linked to notices, exams, or syllabi."""

    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    attachType = models.CharField(max_length=50, null=True, blank=True)
    fileName = models.FileField(upload_to=notice_attach_upload, null=True, blank=True)

    def __str__(self):
        return self.fileName.url if self.fileName else ""


class Notice(models.Model):
    """A notice posted by the school."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    attachments = models.ManyToManyField(Attachment, blank=True)
    read_by_students = models.ManyToManyField("StudentModel", related_name="read_by_students", blank=True)
    read_by_staff = models.ManyToManyField("StaffModel", related_name="read_by_teachers", blank=True)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date_posted"]
        constraints = [
            UniqueConstraint(
                fields=["school", "title", "date_posted"],
                name="unique_notice_per_school",
            ),
        ]

    def __str__(self):
        return self.title


class EventModel(models.Model):
    """A school event."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    attachments = models.ManyToManyField(Attachment, blank=True)
    date = models.DateField()
    title = models.CharField(max_length=50)
    description = models.TextField()
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["school", "date", "title"],
                name="unique_event_per_school_date_title",
            ),
        ]

    def __str__(self):
        return self.title


class ThoughtDayModel(models.Model):
    """Thought of the day."""

    content = models.TextField()
    date = models.DateField()
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)

    def __str__(self):
        return f"Thought - {self.date}"
