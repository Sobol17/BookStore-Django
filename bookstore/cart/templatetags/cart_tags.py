from django import template
from cart.models import Cart
from django.template.context_processors import request

register = template.Library()

@register.simple_tag(takes_context=True)
def get_cart_count(context):
    request = context['request']
    if not request.session.session_key:
        return 0

    try:
        cart = Cart.objects.get(session_key=request.session.session_key)
        return cart.total_items
    except Cart.DoesNotExist:
        return 0


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def dict_get(dictionary, key):
    try:
        return dictionary.get(key)
    except AttributeError:
        return None
