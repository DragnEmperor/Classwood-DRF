import datetime

from rest_framework.validators import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Accounts


def generate_staff_user(first_name, phone, joining):
    """
    Auto-generate an email and password for a staff/student account.
    Email: <first5chars><last3+mid2 of phone>@classwood.com
    Password: <first5chars><dd><mm><last2 of phone>
    """
    email = first_name.lower() + phone[-3:] + phone[3:5] + "@classwood.com"
    if Accounts.objects.filter(email=email).exists():
        raise ValidationError("User already exists with same name and mobile number.")

    if joining is not None:
        if isinstance(joining, str):
            joining = datetime.date.fromisoformat(joining)
        parts = joining.isoformat().split("-")
    else:
        parts = datetime.datetime.now().isoformat().split("-")

    prefix = first_name.lower()[:5].ljust(5, "5")
    password = prefix + parts[2] + parts[1] + phone[-2:]

    return {"email": email, "password": password}


def create_jwt_pair(user):
    """Return an access/refresh token pair for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
