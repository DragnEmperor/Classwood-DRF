# Classwood Backend

Classwood Backend is a Django REST Framework API for the Classwood school management application. It powers school-admin, staff, and student workflows including authentication, classrooms, staff and student records, attendance, timetable management, exams, syllabus, notices, events, and fee tracking.

## Tech Stack

- Python with Django 5.2
- Django REST Framework
- SimpleJWT for token authentication
- drf-spectacular for OpenAPI schema generation
- django-cors-headers for frontend integration
- SQLite by default for local development
- pyotp and email delivery for password reset OTP flows

## Main Capabilities

- School registration, login, logout, JWT refresh, forgot-password OTP, and password reset
- School profile management
- Staff CRUD, staff CSV import, and staff attendance
- Student CRUD, student CSV import, and student attendance
- Classroom creation with class teacher and subject assignments
- Subject, syllabus, timetable, and common-period management
- Exam creation, result upload, manual marks entry, and CSV result import
- Notices, events, sessions, and thought-of-the-day content
- Fee setup, student fee visibility, payment history, and fee summaries
- Role-aware API access for school admins, staff, and students

## Project Structure

```text
Classwood-DRF/
├── classwoodBackend/
│   ├── manage.py
│   ├── classwoodBackend/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   └── api/
│       ├── models/
│       ├── serializers/
│       ├── views/
│       ├── urls.py
│       ├── permissions.py
│       ├── pagination.py
│       ├── services.py
│       ├── utils.py
│       ├── validators.py
│       └── manager.py
├── etc/
│   ├── base.txt
│   ├── dev.txt
│   └── env.txt
└── README.md
```

## Setup

1. Create and activate a virtual environment:

```bash
cd Classwood-DRF
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r etc/base.txt
```

3. Create `.env` in the `Classwood-DRF` directory. Use `etc/env.txt` as the starting point:

```env
DJANGO_SECRET_KEY=replace-with-a-local-secret
DEVELOPMENT=True
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=True
DEFAULT_PAGE_SIZE=5
THROTTLE_ANON=30/min
THROTTLE_USER=120/min
THROTTLE_LOGIN=5/min
EMAIL_USE_TLS=True
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=you@example.com
EMAIL_HOST_PASSWORD=app-password
EMAIL_PORT=587
LOG_LEVEL=INFO
```

4. Run migrations:

```bash
cd classwoodBackend
python manage.py migrate
```

5. Start the API:

```bash
python manage.py runserver
```

The API is served at `http://127.0.0.1:8000/api/`.

## Useful Commands

From `Classwood-DRF/classwoodBackend`:

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

From `Classwood-DRF` when using the checked-in virtual environment path:

```bash
.venv/bin/python classwoodBackend/manage.py check
```

## Pagination

List endpoints use DRF page-number pagination.

Default response shape:

```json
{
  "count": 42,
  "next": "http://127.0.0.1:8000/api/list/classroom/?page=2&page_size=12",
  "previous": null,
  "results": []
}
```

Supported query params:

- `page`: one-based page number
- `page_size`: number of rows requested by the frontend

The default page size is controlled by `DEFAULT_PAGE_SIZE` and falls back to `5`. The maximum `page_size` is `100`.

## API Overview

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/signup/` | Register a school account |
| POST | `/api/login/` | Login and return JWT tokens |
| POST | `/api/logout/` | Logout and blacklist refresh token |
| POST | `/api/refresh-token/` | Refresh JWT access token |
| POST | `/api/forgot-password/` | Send password reset OTP |
| POST | `/api/verify-otp/` | Verify OTP and reset password |

### School Admin

| Method | Endpoint | Description |
| --- | --- | --- |
| GET/PATCH | `/api/account/` | School profile |
| CRUD | `/api/list/staff/` | Staff records |
| CRUD | `/api/list/classroom/` | Classroom records |
| GET | `/api/list/student/` | All students in the school |
| CRUD | `/api/list/notice/` | Notices |
| CRUD | `/api/list/event/` | Events |
| CRUD | `/api/list/session/` | Academic sessions |
| CRUD | `/api/list/staffAttendance/` | Staff attendance |
| CRUD | `/api/list/thoughtDay/` | Thought of the day |
| CRUD | `/api/list/fees/` | Fee definitions and fee summary |
| GET/POST | `/api/list/payments/` | Payment history and payment records |

### Staff

| Method | Endpoint | Description |
| --- | --- | --- |
| GET/PATCH | `/api/staff/me/` | Staff profile |
| CRUD | `/api/staff/classroom/` | Assigned classrooms |
| CRUD | `/api/staff/subject/` | Subjects |
| CRUD | `/api/staff/student/` | Students |
| CRUD | `/api/staff/studentAttendance/` | Student attendance |
| CRUD | `/api/staff/exam/` | Exams and tests |
| CRUD | `/api/staff/result/` | Exam results |
| CRUD | `/api/staff/syllabus/` | Syllabus uploads |
| CRUD | `/api/staff/timeTable/` | Day-wise timetable periods |
| CRUD | `/api/staff/commontime/` | Common periods such as recess or breaks |
| PUT | `/api/staff/exam/mark/<uuid>` | Mark an exam as complete |

### Student

| Method | Endpoint | Description |
| --- | --- | --- |
| GET/PATCH | `/api/student/me/` | Student profile |
| GET | `/api/student/subjects/` | Student subjects |
| GET | `/api/student/syllabus/` | Student syllabus |
| GET | `/api/student/result/` | Student results |
| GET | `/api/student/thoughtDay/` | Thought of the day |
| GET | `/api/student/fees/` | Student fee summary and payments |

## Frontend Integration

The Next.js frontend should call the backend through its proxy route:

```text
/api/backend/<backend-path>
```

Example:

```text
/api/backend/list/classroom/?page=1&page_size=12
```

Authenticated browser requests rely on the frontend proxy attaching the server-side access token from cookies. Direct browser calls to `http://127.0.0.1:8000/api/...` are useful for debugging only when the `Authorization: Bearer <token>` header is supplied manually.

## Development Notes

- Keep paginated list views paginated. Use `count` for totals instead of fetching every page.
- Use a bounded `page_size` for selector data such as class or subject dropdowns.
- Add backend aggregate endpoints when the UI needs exact cross-page metrics, such as total present students for a day.
- File uploads use multipart form data for CSV, profile images, notices, and syllabus attachments.

## License

See [LICENSE](LICENSE).
