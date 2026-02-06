from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('products/bulk-upsert', views.products_bulk_upsert, name='products-bulk-upsert'),
    path('stocks/bulk-update', views.stocks_bulk_update, name='stocks-bulk-update'),
    path('orders', views.orders_list, name='orders-list'),
    path('orders/<str:shop_order_id>/acknowledge', views.order_acknowledge, name='orders-acknowledge'),
    path('orders/<str:shop_order_id>/status', views.order_status_update, name='orders-status-update'),
]
