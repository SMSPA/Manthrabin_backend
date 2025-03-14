import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        user = self.create_user(email, first_name, last_name, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    PublicID = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    password = models.CharField(max_length=255)
    AccountType = models.CharField(max_length=10, choices=[('Admin', 'Admin'), ('User', 'User')], default='User')
    IsActive = models.BooleanField(default=True)
    Created_at = models.DateTimeField(auto_now_add=True)
    Updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email


class PasswordReset(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

class Interest(models.Model):
    InterestID = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=255, unique=True)
    Description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.Title


class UserInterest(models.Model):
    ID = models.AutoField(primary_key=True)
    UserID = models.ForeignKey("users.User", on_delete=models.CASCADE)
    InterestID = models.ForeignKey(Interest, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('UserID', 'InterestID')