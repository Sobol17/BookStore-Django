from django import forms
from django.utils.html import strip_tags


FIELD_STYLES = 'input text-sm font-medium text-ink placeholder:text-ink-muted/70 bg-white/90 border border-accent-soft focus:border-accent focus:ring-2 focus:ring-accent/60'


class OrderForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-black rounded-none text-black placeholder-gray-500 focus:outline-none focus:border-black',
            'placeholder': 'Имя'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-black rounded-none text-black placeholder-gray-500 focus:outline-none focus:border-black',
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
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-black rounded-none text-black placeholder-gray-500 focus:outline-none focus:border-black',
            'placeholder': 'Email (optional)',
        })
    )
    address1 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-black rounded-none text-black placeholder-gray-500 focus:outline-none focus:border-black pr-10',
            'placeholder': 'Адресс'
        })
    )
    address2 = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-black rounded-none text-black placeholder-gray-500 focus:outline-none focus:border-black',
            'placeholder': 'Адресс доп.'
        })
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-black rounded-none text-black placeholder-gray-500 focus:outline-none focus:border-black',
            'placeholder': 'Город'
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-black rounded-none text-black placeholder-gray-500 focus:outline-none focus:border-black',
            'placeholder': 'Postal Code'
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
