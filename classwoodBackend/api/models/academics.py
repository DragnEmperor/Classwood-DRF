from uuid import uuid4

from django.db import models
from django.db.models import UniqueConstraint


class ExamModel(models.Model):
    """An exam for a specific subject in a classroom."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    tag = models.CharField(max_length=50)
    classroom = models.ForeignKey("ClassroomModel", on_delete=models.CASCADE)
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE)
    max_marks = models.IntegerField(default=100)
    attachments = models.ManyToManyField("Attachment", blank=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    date_of_exam = models.DateField()
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_of_exam"]
        constraints = [
            UniqueConstraint(
                fields=["school", "classroom", "subject", "date_of_exam"],
                name="unique_exam_per_school_class_subject_date",
            ),
        ]

    def __str__(self):
        return self.tag


class ResultModel(models.Model):
    """A student's score on an exam."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    student = models.ForeignKey("StudentModel", on_delete=models.CASCADE)
    exam = models.ForeignKey("ExamModel", on_delete=models.CASCADE)
    score = models.IntegerField()
    attachments = models.ManyToManyField("Attachment", blank=True)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    class Meta:
        ordering = ["-exam__date_of_exam"]
        constraints = [
            UniqueConstraint(
                fields=["student", "exam", "session"],
                name="unique_result_per_student_exam_session",
            ),
        ]

    def __str__(self):
        return f"{self.student} - {self.exam}"


class SyllabusModel(models.Model):
    """Syllabus for a subject in a classroom."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    classroom = models.ForeignKey("ClassroomModel", on_delete=models.CASCADE)
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE)
    attachments = models.ManyToManyField("Attachment", blank=True)
    tag = models.CharField(max_length=50, blank=True, null=True)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["school", "classroom", "subject", "session"],
                name="unique_syllabus_per_school_class_subject_session",
            ),
        ]

    def __str__(self):
        return f"{self.subject.name}_{self.tag}"


class TimeTableModel(models.Model):
    """A single timetable slot for a classroom on a given day."""

    DAYS_OF_WEEK = [
        ("0", "Monday"),
        ("1", "Tuesday"),
        ("2", "Wednesday"),
        ("3", "Thursday"),
        ("4", "Friday"),
        ("5", "Saturday"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    classroom = models.ForeignKey("ClassroomModel", related_name="timetables", on_delete=models.CASCADE)
    day = models.CharField(choices=DAYS_OF_WEEK, max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.ForeignKey("Subject", on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey("StaffModel", on_delete=models.SET_NULL, null=True, blank=True)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.classroom} - {self.day} {self.start_time}"


class CommonTimeModel(models.Model):
    """A common-time slot (assembly, recess, etc.) for a classroom."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    school = models.ForeignKey("SchoolModel", on_delete=models.CASCADE)
    classroom = models.ForeignKey("ClassroomModel", related_name="commontime", on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.CharField(max_length=128)
    session = models.ForeignKey("SessionModel", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.classroom} - {self.subject}"
