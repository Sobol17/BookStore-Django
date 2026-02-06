from django.urls import path
from .views import (
    IndexView,
    CatalogView,
    BookPurchaseView,
    ProductDetailView,
    ProductSearchView,
    AuthorSuggestView,
    ProductReviewCreateView,
    ProductStockNotifyView,
    ProductAIReviewView,
)

app_name = 'main'

urlpatterns = [
	path('', IndexView.as_view(), name='index'),
	path('sell-books/', BookPurchaseView.as_view(), name='book_purchase'),
	path('catalog/', CatalogView.as_view(), name='catalog_all'),
	path('catalog/<uslug:category_slug>/', CatalogView.as_view(), name='catalog'),
	path('product/<uslug:slug>/', ProductDetailView.as_view(), name='product_detail'),
	path('product/<uslug:slug>/reviews/new/', ProductReviewCreateView.as_view(), name='product_review_create'),
	path('product/<uslug:slug>/reviews/deepseek/', ProductAIReviewView.as_view(), name='product_deepseek_review'),
	path('product/<uslug:slug>/notify/', ProductStockNotifyView.as_view(), name='product_stock_notify'),
	path('search/', ProductSearchView.as_view(), name='product_search'),
	path('authors/suggest/', AuthorSuggestView.as_view(), name='author_suggest'),
]
