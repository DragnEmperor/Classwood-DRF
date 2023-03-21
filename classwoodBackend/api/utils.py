from . import models
from django.utils.translation import gettext as _
from rest_framework.validators import ValidationError
import datetime

def generate_staff_user(first_name,phone,joining):
    email = first_name.lower() + phone[-3:] + phone[3:5] + "@classwood.com"
    email_exists = models.Accounts.objects.filter(email=email).exists()
    if email_exists:
        res = ValidationError("User already exists with same name, mobile number")
        res.status_code = 200
        raise res
    if joining is not None:
     joining = joining.isoformat().split('-')
    else:
     joining = datetime.datetime.now().isoformat().split('-')
    if len(first_name) > 5:
        first_name = first_name.lower()[0:5]
    else:
        first_name = first_name.lower()[0:len(first_name)] + "5"*(5-len(first_name))
    password = first_name + str(joining[2]) + str(joining[1]) + phone[-2:]
    return {'email':email,'password':password} 