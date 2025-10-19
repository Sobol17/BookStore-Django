from typing import Dict, Iterable, Tuple

from django.db.models import Q, QuerySet
from django.http import QueryDict

CATALOG_FILTERS = {
    'min_price': lambda queryset, value: queryset.filter(price__gte=value),
    'max_price': lambda queryset, value: queryset.filter(price__lte=value),
    'year': lambda queryset, value: queryset.filter(year=value),
    'author': lambda queryset, value: queryset.filter(authors__icontains=value),
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


def is_truthy(value) -> bool:
    if value is None:
        return False
    return str(value).lower() in TRUTHY_VALUES
