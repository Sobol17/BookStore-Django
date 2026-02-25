from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.html import strip_tags


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, first_name, password=None, **extra_fields):
        if not phone:
            raise ValueError('Поле телефон обязательное')
        user = self.model(phone=phone, first_name=first_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)


    def create_superuser(self, phone, first_name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, first_name, password, **extra_fields)



class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    address1 = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(unique=True, max_length=150)

    username = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


    def __str__(self):
        return self.phone


    def clean(self):
        for field in ['company', 'address1', 'address2', 'city', 'postal_code', 'email']:
            value = getattr(self, field)
            if value:
                setattr(self, field, strip_tags(value))

