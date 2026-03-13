from django.urls import path
from .views import CheckoutView, youkassa_webhook

app_name = 'orders'

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('youkassa/webhook/', youkassa_webhook, name='youkassa_webhook'),
]