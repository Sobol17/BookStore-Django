from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags

from common.phone import PhoneValidationError, normalize_phone

User = get_user_model()


FIELD_STYLES = 'input text-sm font-medium text-ink placeholder:text-ink-muted/70 bg-white/90 border border-accent-soft focus:border-accent focus:ring-2 focus:ring-accent/60'
STATIC_SMS_CODE = '1234'


class CustomUserCreationForm(forms.ModelForm):
    sms_code = forms.CharField(
        label='Код из SMS',
        max_length=4,
        widget=forms.TextInput(
            attrs={
                'class': FIELD_STYLES,
                'placeholder': 'Введите код 1234',
                'data-code-input': 'true',
            }
        )
    )

    class Meta:
        model = User
        fields = ('first_name', 'phone')
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': FIELD_STYLES, 'placeholder': 'Имя'}
            ),
            'phone': forms.TextInput(
                attrs={
                    'class': FIELD_STYLES,
                    'placeholder': 'Телефон',
                    'data-phone-input': 'true',
                    'data-phone-mask': 'true',
                    'inputmode': 'tel',
                    'autocomplete': 'tel',
                }
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        try:
            normalized = normalize_phone(phone)
        except PhoneValidationError as exc:
            raise forms.ValidationError(str(exc))
        if User.objects.filter(phone=normalized).exists():
            raise forms.ValidationError('Номер телефона уже зарегистрирован')
        return normalized

    def clean_sms_code(self):
        code = self.cleaned_data.get('sms_code')
        if code != STATIC_SMS_CODE:
            raise forms.ValidationError('Неверный код подтверждения')
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['sms_code'])
        if commit:
            user.save()
        return user


class CustomUserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Телефон",
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': FIELD_STYLES,
                'placeholder': 'Телефон',
                'data-phone-input': 'true',
                'data-phone-mask': 'true',
                'inputmode': 'tel',
                'autocomplete': 'tel',
            }
        )
    )
    password = forms.CharField(
        label="Код из SMS",
        widget=forms.PasswordInput(
            attrs={
                'class': FIELD_STYLES,
                'placeholder': 'Введите код 1234',
                'data-code-input': 'true',
            }
        )
    )

    def clean(self):
        phone = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if phone and password:
            try:
                normalized_phone = normalize_phone(phone)
            except PhoneValidationError as exc:
                raise forms.ValidationError(str(exc))
            self.cleaned_data['username'] = normalized_phone
            self.user_cache = authenticate(self.request, phone=normalized_phone, password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Неверная комбинация телефона и кода')
            elif not self.user_cache.is_active:
                raise forms.ValidationError('Аккаунт деактивирован')
        return self.cleaned_data


class CustomUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': FIELD_STYLES,
                'placeholder': 'Телефон',
                'data-phone-mask': 'true',
                'inputmode': 'tel',
                'autocomplete': 'tel',
            }
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
        required=False,
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
        if not phone:
            return None
        try:
            normalized = normalize_phone(phone)
        except PhoneValidationError as exc:
            raise forms.ValidationError(str(exc))
        if User.objects.filter(phone=normalized).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Этот телефон уже используется')
        return normalized

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('phone'):
            cleaned_data['phone'] = self.instance.phone
        for field in ['company', 'address1', 'address2', 'city', 'postal_code', 'email']:
            if cleaned_data.get(field):
                cleaned_data[field] = strip_tags(cleaned_data[field])
        return cleaned_data
