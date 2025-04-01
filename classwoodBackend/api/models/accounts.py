from uuid import uuid4

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.db.models import UniqueConstraint

from api.manager import CustomUserManager


class Accounts(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the primary identifier."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)

    USERNAME_FIELD = "email"

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def __str__(self):
        return self.email


class BlackListedToken(models.Model):
    """Stores blacklisted JWT tokens for logout support."""

    token = models.CharField(max_length=500)
    user = models.ForeignKey("Accounts", related_name="token_user", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["token", "user"], name="unique_token_user"),
        ]

    def __str__(self):
        return f"Token for {self.user}"


class OTPModel(models.Model):
    """Stores hashed OTPs for password reset."""

    email = models.EmailField()
    hashed_otp = models.CharField(max_length=128)
    expiration_time = models.DateTimeField()

    def __str__(self):
        return f"OTP for {self.email}"
