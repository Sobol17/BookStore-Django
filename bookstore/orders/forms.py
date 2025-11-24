from django import forms
from django.utils.html import strip_tags


FIELD_STYLES = 'w-full rounded-xl border border-accent-soft/80 bg-white/95 px-4 py-3 text-sm font-medium text-ink placeholder:text-ink-muted focus:border-accent focus:ring-2 focus:ring-accent/40'


class OrderForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': FIELD_STYLES,
            'placeholder': 'Имя'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': FIELD_STYLES,
            'placeholder': 'Фамилия'
        })
    )
    phone = forms.CharField(
        label="Телефон",
        required=True,
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
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': FIELD_STYLES,
            'placeholder': 'Email',
            'autocomplete': 'email',
        })
    )
    address1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': FIELD_STYLES,
            'placeholder': 'Адрес'
        })
    )
    address2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': FIELD_STYLES,
            'placeholder': 'Квартира, офис (необязательно)'
        })
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': FIELD_STYLES,
            'placeholder': 'Город'
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': FIELD_STYLES,
            'placeholder': 'Почтовый индекс'
        })
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['address1'].initial = user.address1
            self.fields['address2'].initial = user.address2
            self.fields['city'].initial = user.city
            self.fields['postal_code'].initial = user.postal_code
            self.fields['phone'].initial = user.phone

    def clean(self):
        cleaned_data = super().clean()
        for field in ['address1', 'address2', 'city', 'postal_code', 'phone']:
            if cleaned_data.get(field):
                cleaned_data[field] = strip_tags(cleaned_data[field])
        return cleaned_data
