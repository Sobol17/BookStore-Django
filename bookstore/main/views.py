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


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = kwargs.get('category_slug')
        categories = Category.objects.all()
        product = Product.objects.all().order_by('-created_at')
        current_category = None
        if category_slug:
            current_category = get_object_or_404(Category, slug=category_slug)
            product = product.filter(category=current_category)
        query = self.request.GET.get('q')
        if query:
            product = product.filter(
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
            'current_category': category_slug,
            'filter_params': filter_params,
            'genres': Genre.objects.all(),
            'search_query': query or '',
        })
        if self.request.headers.GET.get('show_search') == True:
            context['show_search'] = True
        elif self.request.headers.GET.get('reset_search') == True:
            context['reset_search'] = True
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            if context.get('show_search'):
                return TemplateResponse(request, 'main/search_input.html', context)
            elif context.get('reset_search'):
                return TemplateResponse(request, 'main/search_button.html', {})
            template = 'main/filter_modal.html' if request.headers.get('show_filter') == True else 'main/catalog.html'
            return TemplateResponse(request, template, context)
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
        context['current_category'] = product.category.slug
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            return TemplateResponse(request, 'main/product_detail.html', context)
        raise TemplateResponse(request, self.template_name, context)