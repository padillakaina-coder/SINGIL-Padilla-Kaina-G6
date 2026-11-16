

# Create your models here.
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('role', 'ADMIN')
        return self.create_user(email, password, **extra)


class User(AbstractUser):
    ROLE_CHOICES = [('USER', 'Registered User'), ('ADMIN', 'Administrator')]

    username = None
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=5, choices=ROLE_CHOICES, default='USER')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = UserManager()

    def __str__(self):
        return self.email