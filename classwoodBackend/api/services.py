"""
Service functions for complex business logic (CSV imports, etc.)
Keeps views thin and serializers focused on validation / single-object creation.
"""

import csv
import datetime

from rest_framework.validators import ValidationError

from api.models import (
    Accounts,
    ClassroomModel,
    ResultModel,
    SessionModel,
    StaffModel,
    StudentModel,
    Subject,
)
from api.utils import generate_staff_user


def _parse_date(value):
    """Parse a date string in YYYY-MM-DD or DD-MM-YYYY format."""
    for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {value}")


def _parse_gender(value):
    mapping = {"M": "1", "F": "2"}
    return mapping.get(value, "3")


# ── Staff CSV Import ──────────────────────────────────────────────────────────


def import_staff_from_csv(csv_file, school, session):
    """
    Import staff records from a CSV file.
    Returns (created_count, errors).
    """
    decoded = csv_file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)
    errors = []
    created = 0

    if session is None:
        session = SessionModel.objects.filter(school=school, is_active=True).order_by("-start_date").first()

    for row_num, row in enumerate(reader, 1):
        if not all(row.values()):
            break
        try:
            doj = _parse_date(row.get("Date of Joining", ""))
            user_data = generate_staff_user(row.get("First Name", ""), row.get("Mobile", ""), doj)
            user = Accounts.objects.create_user(**user_data)
            StaffModel.objects.create(
                user=user,
                first_name=row.get("First Name", ""),
                last_name=row.get("Last Name", ""),
                date_of_birth=_parse_date(row.get("DOB", "")),
                gender=_parse_gender(row.get("Gender")),
                contact_email=row.get("Email") or None,
                mobile_number=row.get("Mobile", ""),
                address=row.get("Address", ""),
                account_no=row.get("Account_no", ""),
                date_of_joining=doj,
                school=school,
                session=session,
            )
            created += 1
        except (ValidationError, ValueError, Exception) as e:
            errors.append({"row": row_num, "errors": str(e)})

    return created, errors


# ── Student CSV Import ─────────────────────────────────────────────────────────


def import_students_from_csv(csv_file, school, session, classroom_id=None):
    """
    Import student records from a CSV file.
    Returns (created_count, errors).
    """
    decoded = csv_file.read().decode("utf-8-sig").splitlines()
    reader = csv.DictReader(decoded)
    errors = []
    created = 0

    if session is None:
        session = SessionModel.objects.filter(school=school, is_active=True).order_by("-start_date").first()

    for row_num, row in enumerate(reader, 1):
        if not all(row.values()):
            break
        try:
            dob = _parse_date(row.get("DOB", ""))
            doa = _parse_date(row.get("Date of Admission", ""))

            # Resolve classroom
            classroom = None
            if classroom_id:
                classroom = ClassroomModel.objects.get(id=classroom_id)
            else:
                classroom = ClassroomModel.objects.get(
                    class_name=row.get("Class", ""),
                    section_name=row.get("Section", ""),
                    school=school,
                    session=session,
                )

            user_data = generate_staff_user(row.get("First Name", ""), row.get("Mobile", ""), doa)
            user = Accounts.objects.create_user(**user_data)

            student = StudentModel.objects.create(
                user=user,
                first_name=row.get("First Name", ""),
                last_name=row.get("Last Name", ""),
                father_name=row.get("Father Name", ""),
                mother_name=row.get("Mother Name", ""),
                date_of_birth=dob,
                gender=_parse_gender(row.get("Gender")),
                contact_email=row.get("Email") or None,
                parent_mobile_number=row.get("Mobile", ""),
                address=row.get("Address", ""),
                roll_no=row.get("Roll No", ""),
                admission_no=row.get("Admission No", ""),
                parent_account_no=row.get("Account_no") or None,
                date_of_admission=doa,
                classroom=classroom,
                school=school,
                session=session,
            )

            # Assign subjects
            subject_str = row.get("Subjects")
            if subject_str:
                for name in subject_str.split(","):
                    try:
                        subj = Subject.objects.get(name=name.strip(), classroom=classroom, session=session)
                        student.subjects.add(subj)
                    except Subject.DoesNotExist:
                        errors.append({"row": row_num, "errors": f"Subject '{name.strip()}' not found"})
            else:
                student.subjects.set(Subject.objects.filter(classroom=classroom, session=session))

            created += 1
        except (ClassroomModel.DoesNotExist, ValidationError, ValueError, Exception) as e:
            errors.append({"row": row_num, "errors": str(e)})

    return created, errors


# ── Result CSV Import ──────────────────────────────────────────────────────────


def import_results_from_csv(csv_file, school, session, exam_id=None, classroom_id=None):
    """
    Import exam results from a CSV file.
    Returns (created_count, errors).
    """
    decoded = csv_file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(decoded)
    errors = []
    created = 0

    if session is None:
        session = SessionModel.objects.filter(school=school, is_active=True).order_by("-start_date").first()

    for row_num, row in enumerate(reader, 1):
        if not all(row.values()):
            break
        try:
            roll_no = row.get("Roll No")
            classroom = None
            if classroom_id:
                classroom = ClassroomModel.objects.get(id=classroom_id)
            else:
                class_name = row.get("Class", "") + row.get("Section", "")
                classroom = ClassroomModel.objects.get(class_name=class_name, school=school, session=session)

            student = StudentModel.objects.get(roll_no=roll_no, classroom=classroom, session=session)
            ResultModel.objects.create(
                student=student,
                exam_id=exam_id,
                score=int(row.get("Marks", 0)),
                session=session,
            )
            created += 1
        except (StudentModel.DoesNotExist, ClassroomModel.DoesNotExist, Exception) as e:
            errors.append({"row": row_num, "errors": str(e)})

    return created, errors
