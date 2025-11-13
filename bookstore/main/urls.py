from django.urls import path
from .views import (
    IndexView,
    CatalogView,
    ProductDetailView,
    ProductSearchView,
    AuthorSuggestView,
    ProductReviewCreateView,
    ProductStockNotifyView,
)

app_name = 'main'

urlpatterns = [
	path('', IndexView.as_view(), name='index'),
	path('catalog/', CatalogView.as_view(), name='catalog_all'),
	path('catalog/<slug:category_slug>/', CatalogView.as_view(), name='catalog'),
	path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
	path('product/<slug:slug>/reviews/new/', ProductReviewCreateView.as_view(), name='product_review_create'),
	path('product/<slug:slug>/notify/', ProductStockNotifyView.as_view(), name='product_stock_notify'),
	path('search/', ProductSearchView.as_view(), name='product_search'),
	path('authors/suggest/', AuthorSuggestView.as_view(), name='author_suggest'),
]
