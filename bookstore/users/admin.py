from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('phone_display', 'first_name_display', 'last_name_display')
    search_fields = ('email', 'first_name', 'last_name',
                     'city')
    ordering = ('email',)
    fieldsets = (
        ('Учетные данные', {'fields': ('email', 'password')}),
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'address1',
                       'address2', 'city', 'postal_code',
                       'phone')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions')
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    add_fieldsets = (
        ('Создание пользователя', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1',
                       'password2', 'is_staff', 'is_active'),
        }),
    )

    @admin.display(description='Телефон', ordering='phone')
    def phone_display(self, obj):
        return obj.phone

    @admin.display(description='Имя', ordering='first_name')
    def first_name_display(self, obj):
        return obj.first_name

    @admin.display(description='Фамилия', ordering='last_name')
    def last_name_display(self, obj):
        return obj.last_name

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        labels = {
            'email': 'Email',
            'password': 'Пароль',
            'password1': 'Пароль',
            'password2': 'Подтверждение пароля',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'address1': 'Адрес (строка 1)',
            'address2': 'Адрес (строка 2)',
            'city': 'Город',
            'postal_code': 'Почтовый индекс',
            'phone': 'Телефон',
            'is_active': 'Активен',
            'is_staff': 'Сотрудник',
            'is_superuser': 'Суперпользователь',
            'groups': 'Группы',
            'user_permissions': 'Права пользователя',
            'last_login': 'Последний вход',
            'date_joined': 'Дата регистрации',
            'username': 'Логин',
        }
        for field_name, label in labels.items():
            if field_name in form.base_fields:
                form.base_fields[field_name].label = label
        if 'username' in form.base_fields:
            form.base_fields['username'].disabled = True

        return form
