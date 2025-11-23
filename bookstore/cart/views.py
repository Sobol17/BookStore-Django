from itertools import product
from statistics import quantiles

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import  View
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.contrib import messages
from django.db import transaction
from .models import Cart, CartItem
from .forms import AddToCartForm, UpdateCartForm
import json

from main.models import Product


class CartMixin:
    def get_cart(self, request):
        if hasattr(request, 'cart'):
            return request.cart

        if not request.session.session_key:
            request.session.create()

        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)

        request.session['card_id'] = cart.id
        request.session.modified = True
        return cart


class CartModalView(CartMixin,View):
    def get(self, request):
        cart = self.get_cart(request)
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product',
            ).order_by('-added_at'),
        }
        return TemplateResponse(request, 'cart/cart_modal.html', context)


class AddToCartView(CartMixin,View):
    @transaction.atomic()
    def post(self, request, slug):
        cart = self.get_cart(request)
        product = get_object_or_404(Product, slug=slug)
        form = AddToCartForm(request.POST, product=product)

        if not form.is_valid():
            return JsonResponse(
                {
                    'error': 'Invalid form data',
                    'errors': form.errors
                },status=400)

        quantity = form.cleaned_data['quantity']
        if product.stock_qty < quantity:
            return JsonResponse({
                'error': 'Not enough stock',
            })

        existing_item = cart.items.filter(
            product=product,
        ).first()

        if existing_item:
            total_quantity = existing_item.quantity + quantity
            if total_quantity > product.stock_qty:
                return JsonResponse({
                    'error': f'Добавлено максимальное количество доступных экземпляров.',
                })

        cart_item = cart.add_product(product, quantity)

        request.session['cart_id'] = cart.id
        request.session.modified = True

        if request.headers.get('HX-request'):
            return redirect('cart:cart_modal')
        else:
            return JsonResponse({
                'success': True,
                'total_items': cart.total_items,
                'message': f'{product.name} добавлен в корзину.',
                'cart_item_id': cart_item.id,
                'quantity': cart_item.quantity,
            })


class UpdateCartItemView(CartMixin,View):
    @transaction.atomic()
    def post(self, request, item_id):
        cart = self.get_cart(request)
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        product = cart_item.product
        cart_item_id = cart_item.id
        new_quantity = cart_item.quantity

        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid quantity.'}, status=400)

        removed = False
        message = ''
        if quantity <= 0:
            cart_item.delete()
            removed = True
            new_quantity = 0
            message = f'«{product.name}» удалена из корзины.'
        else:
            if quantity > cart_item.product.stock_qty:
                return JsonResponse({
                    'error': f'Добавлено максимальное количество доступных экземпляров.',
                }, status=400)

            cart_item.quantity = quantity
            cart_item.save()
            new_quantity = cart_item.quantity
            message = f'Количество «{product.name}» обновлено.'

        request.session['cart_id'] = cart.id
        request.session.modified = True

        context = {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product',
            ).order_by('-added_at'),
        }
        if request.headers.get('HX-Request'):
            response = TemplateResponse(request, 'cart/cart_modal.html', context)
            response['HX-Trigger'] = json.dumps({
                'cart-updated': {
                    'product_id': product.id,
                    'product_slug': product.slug,
                    'cart_item_id': None if removed else cart_item_id,
                    'quantity': new_quantity,
                    'total_items': cart.total_items,
                    'message': message,
                }
            })
            return response

        response_data = {
            'success': True,
            'total_items': cart.total_items,
            'cart_item_id': cart_item_id,
            'quantity': new_quantity,
            'removed': removed,
            'message': message,
        }
        return JsonResponse(response_data)



class RemoveCartItemView(CartMixin,View):
    @transaction.atomic()
    def post(self, request, item_id):
        cart = self.get_cart(request)
        try:
            cart_item = cart.items.get(id=item_id)
            product = cart_item.product
            cart_item_id = cart_item.id
            cart_item.delete()

            request.session['cart_id'] = cart.id
            request.session.modified = True

            context = {
                'cart': cart,
                'cart_items': cart.items.select_related(
                    'product',
                ).order_by('-added_at'),
            }
            if request.headers.get('HX-Request'):
                response = TemplateResponse(request, 'cart/cart_modal.html', context)
                response['HX-Trigger'] = json.dumps({
                    'cart-updated': {
                        'product_id': product.id,
                        'product_slug': product.slug,
                        'cart_item_id': cart_item_id,
                        'quantity': 0,
                        'total_items': cart.total_items,
                        'message': f'«{product.name}» удалена из корзины.',
                    }
                })
                return response
            return JsonResponse({
                'success': True,
                'total_items': cart.total_items,
                'cart_item_id': cart_item_id,
                'removed': True,
                'message': f'«{product.name}» удалена из корзины.',
            })
        except CartItem.DoesNotExist:
            return JsonResponse({
                'error': 'Item not found.',
            }, status=400)


class CartCountView(CartMixin,View):
    def get(self, request):
        cart = self.get_cart(request)
        return JsonResponse({
            'total_items': cart.total_items,
            'subtotal': float(cart.subtotal),
        })


class ClearCartView(CartMixin,View):
    def post(self, request):
        cart = self.get_cart(request)
        cart.clear()
        request.session['cart_id'] = cart.id
        request.session.modified = True

        if request.headers.get('HX-request'):
            context = {
                'cart': cart,
            }
            return TemplateResponse(request, 'cart/cart_empty.html', context)
        return JsonResponse({
            'success': True,
            'message': 'Cart cleared.',
        })


class CartSummaryView(CartMixin,View):
    def get(self, request):
        cart = self.get_cart(request)
        context = {
            'cart': cart,
            'cart_items': cart.items.select_related(
                'product',
            ).order_by('-added_at'),
        }
        return TemplateResponse(request, 'cart/cart_summary.html', context)
