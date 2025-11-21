from django import forms
from .models import ProductReview, BookPurchaseRequest, BookPurchasePhoto


class MultiFileClearableInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ProductReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        initial=5,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = ProductReview
        fields = ('author_name', 'rating', 'text')
        widgets = {
            'author_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Ваше имя',
            }),
            'text': forms.Textarea(attrs={
                'rows': 5,
                'class': 'input resize-none',
                'placeholder': 'Напишите ваш отзыв о товаре',
            }),
        }
        labels = {
            'author_name': 'Ваше имя',
            'text': 'Ваш отзыв',
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating') or 5
        return max(1, min(5, rating))


class BookPurchaseRequestForm(forms.ModelForm):
    photos = forms.ImageField(
        label='Фотографии книги',
        required=False,
        widget=MultiFileClearableInput(
            attrs={
                'multiple': True,
                'accept': 'image/*',
            }
        ),
    )

    class Meta:
        model = BookPurchaseRequest
        fields = ('book_description', 'email', 'phone')
        labels = {
            'book_description': 'Описание экземпляра',
            'email': 'Email',
            'phone': 'Телефон',
        }
        widgets = {
            'book_description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Расскажите о состоянии, тираже и особенностях',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'name@example.com',
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '+7 (900) 000-00-00',
            }),
        }

    def clean_photos(self):
        photos = self.files.getlist('photos')
        for photo in photos:
            content_type = getattr(photo, 'content_type', '') or ''
            if content_type and not content_type.startswith('image/'):
                raise forms.ValidationError('Можно загружать только изображения.')
        return photos

    def save(self, commit=True):
        photos = self.cleaned_data.pop('photos', [])
        instance = super().save(commit=commit)
        if commit:
            for photo in photos:
                BookPurchasePhoto.objects.create(request=instance, image=photo)
        return instance
