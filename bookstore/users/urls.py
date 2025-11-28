from django.urls import path
from .views import (
    register,
    login_view,
    request_email_link,
    request_sms_code,
    email_link_confirm,
    profile_view,
    account_details,
    edit_account_details,
    update_account_details,
    logout_view,
    order_history,
    order_detail,
)

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('login/email/', email_link_confirm, name='email_link_confirm'),
    path('request-email/', request_email_link, name='request_email_link'),
    path('request-sms/', request_sms_code, name='request_sms_code'),
    path('profile/', profile_view, name='profile'),
    path('account-details/', account_details, name='account_details'),
    path('edit-account-details/', edit_account_details, name='edit_account_details'),
    path('update-account-details/', update_account_details, name='update_account_details'),
    path('logout/', logout_view, name='logout'),
    path('orders/', order_history, name='order_history'),
    path('orders/<int:order_id>/', order_detail, name='order_detail'),
]
