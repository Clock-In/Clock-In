from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=256)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name

class UserManager(BaseUserManager):
    def create_user(self, email, password, **kwargs):
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_active', True)
        return self.create_user(email, password, **kwargs)


class User(AbstractUser): # Extend default user model
    username = None # We don't really need usernames, email address is enough.
    email = models.EmailField(_('email address'), unique=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=False, null=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False, null=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.name

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

class Shift(models.Model):
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_assigned_to')
    completed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_completed_by', null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    wage_multiplier = models.FloatField(default=1) # type: ignore

class ShiftSwapRequest(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    message = models.CharField(max_length=512)
    active = models.BooleanField(default=True) # type: ignore

