from django.urls import path
from .views import register, login_view, profile_view, account_details, edit_account_details, update_account_details, \
    logout_view

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('profile/', profile_view, name='profile'),
    path('account-details/', account_details, name='account_details'),
    path('edit-account-details/', edit_account_details, name='edit_account_details'),
    path('update-account-details/', update_account_details, name='update_account_details'),
    path('logout/', logout_view, name='logout'),
    # path('order-history/', views.order_history, name='order_history'),
    # path('order/<int:order_id>/', views.order_detail, name='order_detail'),
]