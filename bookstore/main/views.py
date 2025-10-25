from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from .enums import ProductCollections

from .models import Genre, Product, Banner
from .selectors import (
    get_categories_with_products,
    get_products_collection,
    get_published_products_queryset,
    get_related_products,
)
from .services import apply_catalog_filters, extract_hx_flags


class IndexView(TemplateView):
    template_name = 'main/base.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = get_categories_with_products()
        context['current_category'] = None
        context['is_catalog_page'] = False
        context['new_products'] = get_products_collection(ProductCollections.NEW)
        context['new_products_link'] = reverse('main:catalog_all')
        context['banners'] = Banner.objects.filter(is_active=True).order_by('-created_at')
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/home_content.html', context)
        return TemplateResponse(request, self.template_name, context)


class CatalogView(TemplateView):
    template_name = 'main/base.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        categories = get_categories_with_products()
        products = get_published_products_queryset()
        current_category = None
        if category_slug:
            current_category = get_object_or_404(categories, slug=category_slug)
            products = products.filter(category=current_category)
        products, filter_params, search_query = apply_catalog_filters(
            products,
            self.request.GET,
        )
        context.update({
            'categories': categories,
            'products': products,
            'current_category': current_category.slug if current_category else None,
            'current_category_label': current_category.name if current_category else None,
            'filter_params': filter_params,
            'genres': Genre.objects.all(),
            'search_query': search_query,
            'is_catalog_page': True,
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
        context['related_products'] = get_related_products(product)
        if product.category:
            context['current_category'] = product.category.slug
            context['current_category_label'] = product.category.name
        else:
            context['current_category'] = None
            context['current_category_label'] = None
        context['is_catalog_page'] = False
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/product_detail.html', context)
        return TemplateResponse(request, self.template_name, context)
