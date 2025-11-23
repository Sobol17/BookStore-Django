from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags
from django.core.validators import RegexValidator

User = get_user_model()


FIELD_STYLES = 'input text-sm font-medium text-ink placeholder:text-ink-muted/70 bg-white/90 border border-accent-soft focus:border-accent focus:ring-2 focus:ring-accent/60'


class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(
        required=True,
        validators=[RegexValidator(r'^\+?[0-9]{9,15}$', "Введите корректный номер телефона")],
        widget=forms.TextInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Телефон'}
        )
    )
    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Имя'}
        )
    )
    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Фамилия'}
        )
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Электронная почта'}
        )
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Пароль'}
        )
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Повторите пароль'}
        )
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'email', 'password1', 'password2')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Номер телефона уже зарегистрирован')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = None
        if commit:
            user.save()
        return user


class CustomUserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Телефон",
        required=True,
        validators=[RegexValidator(r'^\+?[0-9]{9,15}$', "Введите корректный номер телефона")],
        widget=forms.TextInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Телефон'}
        )
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Введите пароль'}
        )
    )

    def clean(self):
        phone = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if phone and password:
            self.user_cache = authenticate(self.request, phone=phone, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Неверная комбинация телефона и пароля')
            elif not self.user_cache.is_active:
                raise forms.ValidationError('Аккаунт ')
        return self.cleaned_data


class CustomUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        validators=[RegexValidator(r'^\+?[0-9]{9,15}$', "Введите корректный номер телефона")],
        widget=forms.TextInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Телефон'}
        )
    )
    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Имя'}
        )
    )
    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Фамилия'}
        )
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Электронная почта'}
        )
    )
    company = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': FIELD_STYLES, 'placeholder': 'Компания'}
        )
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'company',
            'address1',
            'address2',
            'city',
            'postal_code',
            'phone',
        )
        widgets = {
            'address1': forms.TextInput(
                attrs={'class': FIELD_STYLES, 'placeholder': 'Адрес'}
            ),
            'address2': forms.TextInput(
                attrs={'class': FIELD_STYLES, 'placeholder': 'Дополнительный адрес'}
            ),
            'city': forms.TextInput(
                attrs={'class': FIELD_STYLES, 'placeholder': 'Город'}
            ),
            'postal_code': forms.TextInput(
                attrs={'class': FIELD_STYLES, 'placeholder': 'Почтовый индекс'}
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and User.objects.filter(phone=phone).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Этот телефон уже используется')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('phone'):
            cleaned_data['phone'] = self.instance.phone
        for field in ['company', 'address1', 'address2', 'city', 'postal_code', 'email']:
            if cleaned_data.get(field):
                cleaned_data[field] = strip_tags(cleaned_data[field])
        return cleaned_data
