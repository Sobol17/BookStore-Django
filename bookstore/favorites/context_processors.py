from .services import resolve_favorite_list


def favorites_processor(request):
    favorite_list = resolve_favorite_list(request)
    favorite_items_map = {}
    if favorite_list:
        for item in favorite_list.items.select_related('product'):
            favorite_items_map[item.product_id] = {
                'favorite_item_id': item.id,
            }

    return {
        'favorite_items_map': favorite_items_map,
        'favorite_total_items': favorite_list.total_items if favorite_list else 0,
    }
