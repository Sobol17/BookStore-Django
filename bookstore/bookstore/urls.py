from django.contrib import admin
from django.urls import path, include, register_converter
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from common.converters import UnicodeSlugConverter

register_converter(UnicodeSlugConverter, 'uslug')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(('api.urls', 'api'), namespace='api')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('favorites/', include('favorites.urls', namespace='favorites')),
    path('users/', include('users.urls', namespace='users')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('', include('main.urls', namespace='main')),
    path('', include('pages.urls', namespace='pages')),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'pages.handlers.not_found_404_view'
