from django.urls import path

from .views import FavoriteListView, ToggleFavoriteView

app_name = 'favorites'


urlpatterns = [
    path('', FavoriteListView.as_view(), name='list'),
    path('toggle/<slug:slug>/', ToggleFavoriteView.as_view(), name='toggle'),
]
