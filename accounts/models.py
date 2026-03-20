from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, password, role, full_name, **kwargs):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, full_name=full_name, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, full_name, role="admin", **kwargs):
        kwargs.setdefault("is_staff", True)
        kwargs.setdefault("is_superuser", True)
        return self.create_user(email, password, role, full_name, **kwargs)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [("admin", "Admin"), ("teacher", "Teacher"), ("student", "Student")]

    email      = models.EmailField(unique=True)
    full_name  = models.CharField(max_length=255)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)   # required for Django admin shell access
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["full_name", "role"]
    objects = UserManager()

    def __str__(self):
        return f"{self.full_name} ({self.email})"

class SystemConfig(models.Model):
    key   = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255)

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    def __str__(self):
        return f"{self.key}: {self.value}"
