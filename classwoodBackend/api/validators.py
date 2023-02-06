from django.core.validators import RegexValidator

mobile_regex = RegexValidator(
    regex="^[0-9]{10,13}$", message="Entered mobile number isn't in a right format!"
)
