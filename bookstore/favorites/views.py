from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.views import View

from main.models import Product

from .models import FavoriteItem
from .services import resolve_favorite_list


class FavoriteMixin:
    def get_favorite_list(self, request):
        if hasattr(request, 'favorite_list') and request.favorite_list:
            return request.favorite_list
        return resolve_favorite_list(request)


class ToggleFavoriteView(FavoriteMixin, View):
    @transaction.atomic
    def post(self, request, slug):
        favorite_list = self.get_favorite_list(request)
        product = get_object_or_404(Product, slug=slug)

        existing_item = favorite_list.items.filter(product=product).first()
        if existing_item:
            existing_item.delete()
            is_favorite = False
            message = f'«{product.name}» удалена из избранного.'
        else:
            FavoriteItem.objects.get_or_create(favorite_list=favorite_list, product=product)
            is_favorite = True
            message = f'«{product.name}» добавлена в избранное.'

        request.session.modified = True

        response_data = {
            'success': True,
            'product_id': product.id,
            'is_favorite': is_favorite,
            'total_items': favorite_list.total_items,
            'message': message,
        }
        return JsonResponse(response_data)


class FavoriteListView(FavoriteMixin, View):
    def get(self, request):
        favorite_list = self.get_favorite_list(request)
        favorite_items = favorite_list.items.select_related('product').order_by('-added_at')
        products = [item.product for item in favorite_items]

        context = {
            'favorite_items': favorite_items,
            'products': products,
            'has_favorites': bool(products),
        }
        return TemplateResponse(request, 'favorites/list.html', context)
