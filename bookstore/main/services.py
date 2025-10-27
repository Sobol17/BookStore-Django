from typing import Dict, Iterable, Tuple
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet
from django.http import QueryDict

CATALOG_FILTERS = {
    'min_price': lambda queryset, value: queryset.filter(price__gte=value),
    'max_price': lambda queryset, value: queryset.filter(price__lte=value),
    'year': lambda queryset, value: queryset.filter(year=value),
    'author': lambda queryset, value: queryset.filter(authors__icontains=value),
    'genre': lambda queryset, value: queryset.filter(genre__slug=value),
}

CATALOG_SORT_OPTIONS = {
    'popular': {
        'label': 'По популярности',
        'order_by': '-created_at',
    },
    'price_asc': {
        'label': 'Цена: по возрастанию',
        'order_by': 'price',
    },
    'price_desc': {
        'label': 'Цена: по убыванию',
        'order_by': '-price',
    },
}

TRUTHY_VALUES = {'1', 'true', 'on', 'yes'}


def apply_catalog_filters(
    products: QuerySet,
    params: QueryDict,
) -> Tuple[QuerySet, Dict[str, str], str]:
    """
    Применяет поисковый запрос и набор фильтров из QueryDict к переданному queryset.
    Возвращает обновлённый queryset, словарь текущих параметров фильтра и строку поиска.
    """
    query = params.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(authors__icontains=query)
            | Q(publisher__icontains=query)
        )

    filter_params: Dict[str, str] = {}
    for key, filter_func in CATALOG_FILTERS.items():
        value = params.get(key)
        if value:
            products = filter_func(products, value)
            filter_params[key] = value
        else:
            filter_params[key] = ''

    filter_params['q'] = query or ''
    return products, filter_params, query or ''

def apply_catalog_sorting(products: QuerySet, sort_key: str) -> Tuple[QuerySet, str]:
    """
    Применяет сортировку к queryset каталога. Возвращает отсортированный queryset и ключ сортировки.
    """
    if sort_key not in CATALOG_SORT_OPTIONS:
        sort_key = 'popular'
    order_by = CATALOG_SORT_OPTIONS[sort_key]['order_by']
    return products.order_by(order_by), sort_key


def extract_hx_flags(
    params: QueryDict,
    keys: Iterable[str] = ('show_search', 'reset_search', 'show_filter', 'reset_filter'),
) -> Dict[str, bool]:
    """
    Извлекает флаги, переданные через hx-vals, преобразуя строковые значения в bool.
    """
    flags: Dict[str, bool] = {}
    for key in keys:
        if is_truthy(params.get(key)):
            flags[key] = True
    return flags


def build_genre_filters(request, genres):
        existing_params = {
            key: value
            for key, value in request.GET.items()
            if key not in {'genre', 'page'} and value
        }
        active_genre = request.GET.get('genre')
        filters = []
        for genre in genres:
            params = existing_params.copy()
            params['genre'] = genre.slug
            query_string = urlencode(params)
            url = f'{request.path}?{query_string}' if query_string else request.path
            filters.append({
                'label': genre.name,
                'slug': genre.slug,
                'url': url,
                'is_active': active_genre == genre.slug,
            })
        reset_query = urlencode(existing_params)
        reset_url = f'{request.path}?{reset_query}' if reset_query else request.path
        return filters, reset_url


def build_pagination(request, page_obj):
        paginator = page_obj.paginator
        if paginator.count == 0:
            return {}
        base_params = {
            key: value
            for key, value in request.GET.items()
            if key != 'page' and value
        }

        def build_url(page_number: int) -> str:
            params = base_params.copy()
            if page_number != 1:
                params['page'] = page_number
            query = urlencode(params)
            return f'{request.path}?{query}' if query else request.path

        ellipsis_token = getattr(Paginator, 'ELLIPSIS', '...')
        if hasattr(paginator, 'get_elided_page_range'):
            page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=1, on_ends=1)
        else:
            page_range = paginator.page_range

        links = []
        for item in page_range:
            if item == ellipsis_token:
                links.append({'label': '…', 'is_gap': True})
                continue
            page_number = int(item)
            links.append({
                'label': str(item),
                'number': page_number,
                'url': build_url(page_number),
                'is_current': page_number == page_obj.number,
            })

        prev_url = build_url(page_obj.previous_page_number()) if page_obj.has_previous() else None
        next_url = build_url(page_obj.next_page_number()) if page_obj.has_next() else None

        return {
            'links': links,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_url': prev_url,
            'next_url': next_url,
        }

def build_sorting_options(request, current_sort: str):
        """
        Формирует список доступных вариантов сортировки с учётом текущих query-параметров.
        """
        base_params = {
            key: value
            for key, value in request.GET.items()
            if key not in {'sort', 'page'} and value
        }
        options = []
        for key, meta in CATALOG_SORT_OPTIONS.items():
            params = base_params.copy()
            if key != 'popular':
                params['sort'] = key
            query_string = urlencode(params)
            url = f'{request.path}?{query_string}' if query_string else request.path
            options.append({
                'key': key,
                'label': meta['label'],
                'url': url,
                'is_active': key == current_sort,
            })
        return options

def is_truthy(value) -> bool:
    if value is None:
        return False
    return str(value).lower() in TRUTHY_VALUES
