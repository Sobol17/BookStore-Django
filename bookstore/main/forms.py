from django import forms
from .models import ProductReview


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
