from urllib.parse import urlencode

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.template.response import TemplateResponse
from django.urls import reverse
from .deepseek import (
    DeepSeekAPIError,
    DeepSeekConfigurationError,
    DeepSeekReviewService,
)
from .enums import ProductCollections

from cart.models import Cart

from .models import Genre, Product, Banner
from .forms import ProductReviewForm, BookPurchaseRequestForm
from .selectors import (
    get_categories_with_products,
    get_products_collection,
    get_published_products_queryset,
    get_related_products,
)
from .services import (
    build_genre_filters,
    build_pagination,
    apply_catalog_filters,
    apply_catalog_sorting,
    build_sorting_options,
    extract_hx_flags,
    extract_selected_authors,
    CATALOG_SORT_OPTIONS,
)


def build_product_reviews_context(product):
    reviews_qs = product.reviews.filter(is_public=True)
    total = reviews_qs.count()
    average = reviews_qs.aggregate(avg=Avg('rating'))['avg'] or 0
    average_display = f'{average:.1f}' if average else '0'
    return {
        'product': product,
        'reviews': reviews_qs,
        'reviews_total': total,
        'reviews_average': average,
        'reviews_average_display': average_display,
    }


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IndexView(TemplateView):
    template_name = 'main/base.html'
    form_class = BookPurchaseRequestForm

    def get_context_data(self, **kwargs):
        purchase_form = kwargs.pop('purchase_form', None)
        purchase_form_success = kwargs.pop('purchase_form_success', None)
        context = super().get_context_data(**kwargs)
        context['categories'] = get_categories_with_products()
        context['current_category'] = None
        context['is_catalog_page'] = False
        context['new_products'] = get_products_collection(ProductCollections.NEW)
        context['new_products_link'] = reverse('main:catalog_all')
        context['banners'] = Banner.objects.filter(is_active=True).order_by('-created_at')
        if purchase_form is None:
            purchase_form = self.form_class()
        context['purchase_form'] = purchase_form
        if purchase_form_success is None:
            purchase_form_success = self.request.GET.get('purchase_submitted') == '1'
        context['purchase_form_success'] = purchase_form_success
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return TemplateResponse(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                context = self.get_context_data(
                    purchase_form=self.form_class(),
                    purchase_form_success=True,
                )
                return TemplateResponse(
                    request,
                    'main/partials/_book_purchase_form.html',
                    context,
                )
            redirect_url = f"{reverse('main:index')}?purchase_submitted=1"
            return HttpResponseRedirect(redirect_url)
        context = self.get_context_data(
            purchase_form=form,
            purchase_form_success=False,
        )
        if request.headers.get('HX-Request'):
            return TemplateResponse(
                request,
                'main/partials/_book_purchase_form.html',
                context,
                status=400,
            )
        return TemplateResponse(request, self.template_name, context)


class BookPurchaseView(TemplateView):
    template_name = 'main/book_purchase.html'
    form_class = BookPurchaseRequestForm

    def get_context_data(self, **kwargs):
        purchase_form = kwargs.pop('purchase_form', None)
        purchase_form_success = kwargs.pop('purchase_form_success', None)
        context = super().get_context_data(**kwargs)
        if purchase_form is None:
            purchase_form = self.form_class()
        context['purchase_form'] = purchase_form
        if purchase_form_success is None:
            purchase_form_success = self.request.GET.get('purchase_submitted') == '1'
        context['purchase_form_success'] = purchase_form_success
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return TemplateResponse(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                context = self.get_context_data(
                    purchase_form=self.form_class(),
                    purchase_form_success=True,
                )
                return TemplateResponse(
                    request,
                    'main/partials/_book_purchase_form.html',
                    context,
                )
            redirect_url = f"{reverse('main:book_purchase')}?purchase_submitted=1"
            return HttpResponseRedirect(redirect_url)
        context = self.get_context_data(
            purchase_form=form,
            purchase_form_success=False,
        )
        if request.headers.get('HX-Request'):
            return TemplateResponse(
                request,
                'main/partials/_book_purchase_form.html',
                context,
                status=400,
            )
        return TemplateResponse(request, self.template_name, context)


class CatalogView(TemplateView):
    template_name = 'main/base.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        categories = get_categories_with_products()
        products = get_published_products_queryset()
        base_products = products
        current_category = None
        if category_slug:
            current_category = get_object_or_404(categories, slug=category_slug)
            products = products.filter(category=current_category)
            base_products = base_products.filter(category=current_category)
        products, filter_params, search_query, price_bounds, year_bounds = apply_catalog_filters(
            products,
            self.request.GET,
        )
        products, current_sort = apply_catalog_sorting(
            products,
            self.request.GET.get('sort', 'popular'),
        )
        sort_options = build_sorting_options(self.request, current_sort)

        genres = Genre.objects.filter(category=current_category) if current_category else Genre.objects.all()
        genres = list(genres)
        all_genres = list(Genre.objects.select_related('category').all())
        params_without_author = self.request.GET.copy()
        params_without_author.setlist('author', [])
        params_without_author['author'] = ''
        authors_filtered, _, _, _, _ = apply_catalog_filters(
            base_products,
            params_without_author,
        )
        authors_list = list(
            authors_filtered.exclude(authors='')
            .values_list('authors', flat=True)
            .distinct()
            .order_by('authors')
        )
        selected_authors = extract_selected_authors(self.request.GET)
        paginator = Paginator(products, 15)
        page_obj = paginator.get_page(self.request.GET.get('page'))
        pagination = build_pagination(self.request, page_obj)
        genre_filters, genre_reset_url = build_genre_filters(self.request, genres)
        active_genres = [
            slug for slug in filter_params.get('genre', '').split(',') if slug
        ]
        active_genre_value = ','.join(active_genres)
        filter_params['sort'] = current_sort
        context.update({
            'categories': categories,
            'products': page_obj,
            'current_category': current_category.slug if current_category else None,
            'current_category_label': current_category.name if current_category else None,
            'filter_params': filter_params,
            'price_bounds': price_bounds,
            'year_bounds': year_bounds,
            'genres': genres,
            'genre_filters': genre_filters,
            'genre_reset_url': genre_reset_url,
            'active_genre': active_genre_value,
            'active_genres': active_genres,
            'all_genres': all_genres,
            'search_query': search_query,
            'authors': authors_list,
            'selected_authors': selected_authors,
            'is_catalog_page': True,
            'is_paginated': paginator.num_pages > 1,
            'page_obj': page_obj,
            'pagination': pagination,
            'sort_options': sort_options,
            'current_sort': current_sort,
            'current_sort_label': CATALOG_SORT_OPTIONS[current_sort]['label'],
        })
        context.update(extract_hx_flags(self.request.GET))
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            if context.get('show_search'):
                return TemplateResponse(request, 'main/search_input.html', context)
            elif context.get('reset_search'):
                return TemplateResponse(request, 'main/search_button.html', {})
            if context.get('show_filter'):
                return TemplateResponse(request, 'main/filter_modal.html', context)
            if context.get('reset_filter'):
                return HttpResponse('')
            return TemplateResponse(request, 'main/catalog.html', context)
        return TemplateResponse(request, self.template_name, context)


class ProductDetailView(DetailView):
    model = Product
    template_name = 'main/base.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['categories'] = get_categories_with_products()
        context['related_products'] = get_related_products(product, limit=8)
        gallery_images = []
        if product.main_image:
            gallery_images.append({
                'url': product.main_image.url,
                'alt': f'Обложка: {product.name}',
            })
        for image in product.images.order_by('position', 'id'):
            gallery_images.append({
                'url': image.image.url,
                'alt': image.alt_text or product.name,
            })
        context['gallery_images'] = gallery_images
        context['seo_text'] = getattr(product, 'seo_text', None) or product.meta_description or product.description
        rating_value = getattr(product, 'rating', None)
        reviews_count = (
            getattr(product, 'reviews_count', None)
            or getattr(product, 'review_count', None)
        )
        if rating_value is not None:
            try:
                rating_value = float(rating_value)
            except (TypeError, ValueError):
                rating_value = None
        if reviews_count is not None:
            try:
                reviews_count = int(reviews_count)
            except (TypeError, ValueError):
                reviews_count = None
        stars = []
        if rating_value:
            full = int(rating_value)
            remainder = rating_value - full
            for _ in range(min(full, 5)):
                stars.append('full')
            if len(stars) < 5 and remainder >= 0.5:
                stars.append('half')
            while len(stars) < 5:
                stars.append('empty')
        else:
            stars = ['empty'] * 5
        context['rating_value'] = rating_value
        context['reviews_count'] = reviews_count
        context['rating_stars'] = stars
        discount_percent = None
        if product.old_price:
            try:
                discount_percent = int(
                    max(0, round((1 - (product.price / product.old_price)) * 100))
                )
            except (TypeError, ZeroDivisionError):
                discount_percent = None
        context['discount_percent'] = discount_percent
        if product.category:
            context['current_category'] = product.category.slug
            context['current_category_label'] = product.category.name
        else:
            context['current_category'] = None
            context['current_category_label'] = None
        context['is_catalog_page'] = False
        context['can_request_ai_review'] = bool(getattr(settings, 'DEEPSEEK_API_KEY', ''))
        cart = None
        if not self.request.session.session_key:
            self.request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=self.request.session.session_key)
        cart_item = cart.items.filter(product=product).first()
        context['product_cart_item'] = cart_item
        context['product_cart_quantity'] = cart_item.quantity if cart_item else 0
        context.update(build_product_reviews_context(product))
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/product_detail.html', context)
        return TemplateResponse(request, self.template_name, context)


class ProductSearchView(TemplateView):
    template_name = 'main/search_results.html'


class ProductReviewCreateView(View):
    template_name = 'main/partials/review_modal.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = ProductReviewForm()
        context = {
            'form': form,
            'product': self.product,
            'initial_rating': form.fields['rating'].initial or 5,
        }
        return TemplateResponse(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = ProductReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = self.product
            review.save()
            context = build_product_reviews_context(self.product)
            response = TemplateResponse(request, 'main/partials/_product_reviews.html', context)
            response['HX-Trigger'] = 'close-review-modal'
            return response
        try:
            initial_rating = int(form.data.get('rating'))
        except (TypeError, ValueError):
            initial_rating = form.fields['rating'].initial or 5
        context = {
            'form': form,
            'product': self.product,
            'initial_rating': initial_rating,
        }
        return TemplateResponse(request, self.template_name, context, status=400)


class ProductStockNotifyView(View):
    template_name = 'main/partials/stock_notify_modal.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {'product': self.product}
        return TemplateResponse(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        email = (request.POST.get('email') or '').strip()
        if not email:
            context = {
                'product': self.product,
                'error': 'Укажите корректный email',
            }
            return TemplateResponse(request, self.template_name, context, status=400)
        return TemplateResponse(
            request,
            'main/partials/stock_notify_success.html',
            {'product': self.product, 'email': email},
        )


class ProductAIReviewView(View):
    template_name = 'main/partials/_product_ai_review.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, slug=kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        context = {
            'product': self.product,
            'initial': False,
        }
        try:
            service = self._build_service()
            context['review_text'] = service.generate_review(
                title=self.product.name,
                authors=self.product.authors,
                year=self.product.year,
                genre=self.product.genre.name if self.product.genre else None,
            )
        except DeepSeekConfigurationError:
            context['error'] = 'Интеграция DeepSeek не настроена.'
        except DeepSeekAPIError as exc:
            context['error'] = str(exc) or 'Не удалось получить рецензию. Попробуйте позже.'
        return TemplateResponse(request, self.template_name, context)

    def _build_service(self) -> DeepSeekReviewService:
        return DeepSeekReviewService(
            api_key=getattr(settings, 'DEEPSEEK_API_KEY', ''),
            api_url=getattr(settings, 'DEEPSEEK_API_URL', 'https://api.deepseek.com/chat/completions'),
            model=getattr(settings, 'DEEPSEEK_MODEL', 'deepseek-chat'),
            timeout=getattr(settings, 'DEEPSEEK_TIMEOUT', 30),
        )

class AuthorSuggestView(View):
    """
    Возвращает список подсказок по авторам в формате JSON.
    """
    max_results = 8

    def get(self, request, *args, **kwargs):
        query = (request.GET.get('q') or '').strip()
        products = get_published_products_queryset().exclude(authors='')
        if query:
            products = products.filter(authors__icontains=query)
        raw_authors = products.values_list('authors', flat=True).distinct()
        suggestions = []
        normalized_query = query.lower()
        separators = [',', ';', '/']
        for entry in raw_authors:
            if not entry:
                continue
            normalized_entry = entry
            for separator in separators[1:]:
                normalized_entry = normalized_entry.replace(separator, separators[0])
            parts = [part.strip() for part in normalized_entry.split(separators[0])]
            for part in parts:
                if not part:
                    continue
                if query and normalized_query not in part.lower():
                    continue
                if part not in suggestions:
                    suggestions.append(part)
                if len(suggestions) >= self.max_results:
                    break
            if len(suggestions) >= self.max_results:
                break
        return JsonResponse({'results': suggestions})
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        products_queryset = get_published_products_queryset()
        filtered_products, _, search_query, _, _ = apply_catalog_filters(
            products_queryset,
            self.request.GET,
        )
        if not search_query:
            filtered_products = products_queryset.none()
        limited_products = filtered_products[:12]
        context.update({
            'products': limited_products,
            'search_query': search_query,
        })
        return context
