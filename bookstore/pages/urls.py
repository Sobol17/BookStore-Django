from django.urls import path
from .views import AboutPageView, ContactsPageView, PageDetailView


app_name = 'pages'

urlpatterns = [
	path('about', AboutPageView.as_view(), name='about'),
	path('about/', AboutPageView.as_view()),
	path('contacts', ContactsPageView.as_view(), name='contacts'),
	path('contacts/', ContactsPageView.as_view()),
	path('<uslug:slug>/', PageDetailView.as_view(), name='page'),
]
