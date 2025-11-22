from .models import Cart


def cart_processor(request):
    if not request.session.session_key:
        request.session.create()

    cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    cart_items_map = {}
    for item in cart.items.all():
        cart_items_map[item.product_id] = {
            'cart_item_id': item.id,
            'quantity': item.quantity,
        }

    return {
        'cart_total_items': cart.total_items,
        'cart_subtotal': cart.subtotal,
        'cart_items_map': cart_items_map,
    }
