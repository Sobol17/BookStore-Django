from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.http import HttpResponse
from django.template.response import TemplateResponse
from .models import Category, Genre, Product
from django.db.models import Q


class IndexView(TemplateView):
    template_name = 'main/base.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = None
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/home_content.html', context)
        return TemplateResponse(request, self.template_name, context)


class CatalogView(TemplateView):
    template_name = 'main/base.html'

    FILTER_MAPPING = {
        'min_price': lambda queryset, value: queryset.filter(price__gte=value),
        'max_price': lambda queryset, value: queryset.filter(price__lte=value),
        'year': lambda queryset, value: queryset.filter(year=value),
        'author': lambda queryset, value: queryset.filter(authors__icontains=value),
    }

    @staticmethod
    def _is_truthy(value):
        if value is None:
            return False
        return str(value).lower() in {'1', 'true', 'on', 'yes'}


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        categories = Category.objects.all()
        products = Product.objects.all().order_by('-created_at')
        current_category = None
        if category_slug:
            current_category = get_object_or_404(Category, slug=category_slug)
            products = products.filter(category=current_category)
        query = self.request.GET.get('q')
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(authors__icontains=query) | Q(publisher__icontains=query)
            )
        filter_params = {}
        for param, filter_func in self.FILTER_MAPPING.items():
            value = self.request.GET.get(param)
            if value:
                products = filter_func(products, value)
                filter_params[param] = value
            else:
                filter_params[param] = ''
        filter_params['q'] = query or ''
        context.update({
            'categories': categories,
            'products': products,
            'current_category': current_category.slug if current_category else None,
            'current_category_label': current_category.name if current_category else None,
            'filter_params': filter_params,
            'genres': Genre.objects.all(),
            'search_query': query or '',
        })
        if self._is_truthy(self.request.GET.get('show_search')):
            context['show_search'] = True
        if self._is_truthy(self.request.GET.get('reset_search')):
            context['reset_search'] = True
        if self._is_truthy(self.request.GET.get('show_filter')):
            context['show_filter'] = True
        if self._is_truthy(self.request.GET.get('reset_filter')):
            context['reset_filter'] = True
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
        context['categories'] = Category.objects.all()
        context['related_products'] = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]
        if product.category:
            context['current_category'] = product.category.slug
            context['current_category_label'] = product.category.name
        else:
            context['current_category'] = None
            context['current_category_label'] = None
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/product_detail.html', context)
        return TemplateResponse(request, self.template_name, context)
