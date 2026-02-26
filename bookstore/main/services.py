from typing import Dict, Iterable, Tuple, List
from urllib.parse import urlencode
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet, Min, Max
from django.http import QueryDict

CATALOG_FILTERS = {
    'min_price': lambda queryset, value: queryset.filter(price__gte=value),
    'max_price': lambda queryset, value: queryset.filter(price__lte=value),
    'min_year': lambda queryset, value: queryset.filter(year__gte=value),
    'max_year': lambda queryset, value: queryset.filter(year__lte=value),
    'year': lambda queryset, value: queryset.filter(year=value),
}

PRICE_PRESETS = [
    {'key': 'lt_300', 'label': 'до 300 ₽', 'min': None, 'max': 300},
    {'key': 'lt_1500', 'label': 'до 1500 ₽', 'min': None, 'max': 1500},
    {'key': '1500_3000', 'label': '1500–3000 ₽', 'min': 1500, 'max': 3000},
    {'key': 'gt_3000', 'label': '3000 ₽ и дороже', 'min': 3000, 'max': None},
]
YEAR_ROUND_TO = 10

CATALOG_SORT_OPTIONS = {
    'popular': {
        'label': 'По популярности',
        'order_by': '-created_at',
    },
    'new': {
        'label': 'Новинки',
        'order_by': 'new',
    },
    'price_asc': {
        'label': 'Дешевле',
        'order_by': 'price',
    },
    'price_desc': {
        'label': 'Дороже',
        'order_by': '-price',
    },
}

TRUTHY_VALUES = {'1', 'true', 'on', 'yes'}


def extract_selected_genres(params: QueryDict) -> List[str]:
    """
    Возвращает список выбранных жанров из QueryDict с сохранением порядка.
    Поддерживает как повторяющиеся параметры genre, так и значения через запятую.
    """
    raw_values = params.getlist('genre')
    if not raw_values:
        single_value = params.get('genre')
        if single_value:
            raw_values = [single_value]
    selected: List[str] = []
    for raw in raw_values:
        if not raw:
            continue
        for slug in raw.split(','):
            clean_slug = slug.strip()
            if clean_slug and clean_slug not in selected:
                selected.append(clean_slug)
    return selected


def extract_selected_authors(params: QueryDict) -> List[str]:
    raw_values = params.getlist('author')
    if not raw_values:
        single_value = params.get('author')
        if single_value:
            raw_values = [single_value]
    selected: List[str] = []
    for raw in raw_values:
        if not raw:
            continue
        for name in raw.split(','):
            clean_name = name.strip()
            if clean_name and clean_name not in selected:
                selected.append(clean_name)
    return selected


def extract_selected_vinyl_directtions(params: QueryDict) -> List[str]:
    raw_values = params.getlist('directtion')
    if not raw_values:
        single_value = params.get('directtion')
        if single_value:
            raw_values = [single_value]
    if not raw_values:
        raw_values = params.getlist('direction')
    if not raw_values:
        single_value = params.get('direction')
        if single_value:
            raw_values = [single_value]
    selected: List[str] = []
    for raw in raw_values:
        if not raw:
            continue
        for value in raw.split(','):
            cleaned = value.strip()
            if cleaned and cleaned not in selected:
                selected.append(cleaned)
    return selected


def determine_price_step(span: int) -> int:
    """
    Возвращает шаг слайдера цены в зависимости от диапазона значений.
    """
    if span <= 100:
        return 1
    if span <= 500:
        return 5
    if span <= 2_000:
        return 10
    if span <= 5_000:
        return 25
    if span <= 20_000:
        return 50
    if span <= 100_000:
        return 100
    if span <= 500_000:
        return 250
    if span <= 1_000_000:
        return 500
    if span <= 2_000_000:
        return 1_000
    return 5_000


def build_price_bounds(queryset: QuerySet) -> Dict[str, int]:
    """
    Определяет минимальную и максимальную цену доступных товаров для текущего среза каталога.
    """
    aggregates = queryset.aggregate(
        min_price=Min('price'),
        max_price=Max('price'),
    )
    min_value = aggregates.get('min_price')
    max_value = aggregates.get('max_price')
    try:
        min_value = int(min_value)
    except (TypeError, ValueError):
        min_value = 0
    try:
        max_value = int(max_value)
    except (TypeError, ValueError):
        max_value = min_value
    if max_value < min_value:
        max_value = min_value
    span = max_value - min_value
    if span <= 0:
        span = 1
        max_value = min_value + span
    step = determine_price_step(span)
    return {
        'min': min_value,
        'max': max_value,
        'step': step,
        'gap': 0,
    }


def build_year_bounds(queryset: QuerySet) -> Dict[str, int]:
    aggregates = queryset.aggregate(
        min_year=Min('year'),
        max_year=Max('year'),
    )
    min_value = aggregates.get('min_year')
    max_value = aggregates.get('max_year')
    try:
        min_value = int(min_value)
    except (TypeError, ValueError):
        min_value = 0
    try:
        max_value = int(max_value)
    except (TypeError, ValueError):
        max_value = min_value
    if max_value < min_value:
        max_value = min_value
    if max_value == min_value:
        max_value = min_value + 1
    return {'min': min_value, 'max': max_value}


def build_year_presets(bounds: Dict[str, int]) -> List[Dict[str, int]]:
    import datetime

    min_year = bounds.get('min', 0) or 0
    max_year = bounds.get('max', min_year + 1) or (min_year + 1)
    current_year = datetime.date.today().year

    # align start to the closest lower decade
    start_year = (min_year // YEAR_ROUND_TO) * YEAR_ROUND_TO if YEAR_ROUND_TO else min_year
    if start_year <= 0:
        start_year = 1900

    presets: List[Dict[str, int]] = []
    cursor = start_year
    while cursor <= current_year:
        upper = cursor + YEAR_ROUND_TO
        label_end = upper if upper < current_year else current_year
        presets.append({
            'key': f'year_{cursor}_{label_end}',
            'label': f'{cursor}–{label_end}',
            'min': cursor,
            'max': label_end,
        })
        cursor = upper

    return presets


def apply_catalog_filters(
    products: QuerySet,
    params: QueryDict,
) -> Tuple[QuerySet, Dict[str, str], str, Dict[str, int], Dict[str, int]]:
    """
    Применяет поисковый запрос и набор фильтров из QueryDict к переданному queryset.
    Возвращает обновлённый queryset, словарь текущих параметров фильтра, строку поиска
    и вычисленные границы цен/годов для текущего набора товаров.
    """
    query = params.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(authors__icontains=query)
            | Q(publisher__icontains=query)
        )

    filter_params: Dict[str, str] = {
        'min_price': '',
        'max_price': '',
        'price_range': params.get('price_range', ''),
        'min_year': '',
        'max_year': '',
        'year_range': params.get('year_range', ''),
        'author': '',
        'directtion': '',
    }
    price_keys = {'min_price', 'max_price'}
    year_keys = {'min_year', 'max_year'}
    multi_keys = {'genre'}
    for key, filter_func in CATALOG_FILTERS.items():
        if key in price_keys or key in multi_keys or key in year_keys:
            continue
        value = params.get(key)
        if value:
            products = filter_func(products, value)
            filter_params[key] = value
        else:
            filter_params[key] = ''

    selected_genres = extract_selected_genres(params)
    if selected_genres:
        products = products.filter(genre__slug__in=selected_genres)
        filter_params['genre'] = ','.join(selected_genres)
    else:
        filter_params['genre'] = ''

    selected_authors = extract_selected_authors(params)
    if selected_authors:
        products = products.filter(authors__in=selected_authors)
        filter_params['author'] = ','.join(selected_authors)
    else:
        filter_params['author'] = ''

    selected_vinyl_directtions = extract_selected_vinyl_directtions(params)
    if selected_vinyl_directtions:
        products = products.filter(attributes__vinyl_directtion__in=selected_vinyl_directtions)
        filter_params['directtion'] = ','.join(selected_vinyl_directtions)
    else:
        filter_params['directtion'] = ''

    price_bounds = build_price_bounds(products)
    price_bounds['presets'] = PRICE_PRESETS
    year_bounds = build_year_bounds(products)
    year_bounds['presets'] = build_year_presets(year_bounds)

    price_range = params.get('price_range')
    if price_range:
        filter_params['price_range'] = price_range
    if price_range:
        preset = next((p for p in PRICE_PRESETS if p['key'] == price_range), None)
        if preset:
            if preset['min'] is not None:
                products = CATALOG_FILTERS['min_price'](products, preset['min'])
                filter_params['min_price'] = str(preset['min'])
            if preset['max'] is not None:
                products = CATALOG_FILTERS['max_price'](products, preset['max'])
                filter_params['max_price'] = str(preset['max'])
    if not price_range:
        for key in ('min_price', 'max_price'):
            filter_func = CATALOG_FILTERS[key]
            value = params.get(key)
            if value:
                products = filter_func(products, value)
                filter_params[key] = value
            else:
                filter_params[key] = ''

    year_range = params.get('year_range')
    if year_range:
        filter_params['year_range'] = year_range
    if year_range:
        preset = next((p for p in year_bounds['presets'] if p['key'] == year_range), None)
        if preset:
            if preset['min'] is not None:
                products = CATALOG_FILTERS['min_year'](products, preset['min'])
                filter_params['min_year'] = str(preset['min'])
            if preset['max'] is not None:
                products = CATALOG_FILTERS['max_year'](products, preset['max'])
                filter_params['max_year'] = str(preset['max'])
    if not year_range:
        for key in ('min_year', 'max_year'):
            filter_func = CATALOG_FILTERS[key]
            value = params.get(key)
            if value:
                products = filter_func(products, value)
                filter_params[key] = value
            else:
                filter_params[key] = ''

    filter_params['q'] = query or ''
    return products, filter_params, query or '', price_bounds, year_bounds

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
        selected_genres = extract_selected_genres(request.GET)
        selected_set = set(selected_genres)
        base_params = {
            key: value
            for key, value in request.GET.items()
            if key not in {'genre', 'page'} and value
        }

        def build_url(slugs: List[str]) -> str:
            params = base_params.copy()
            if slugs:
                params['genre'] = ','.join(slugs)
            query_string = urlencode(params)
            return f'{request.path}?{query_string}' if query_string else request.path

        filters = []
        for genre in genres:
            if genre.slug in selected_set:
                updated = [slug for slug in selected_genres if slug != genre.slug]
            else:
                updated = selected_genres + [genre.slug]
            filters.append({
                'label': genre.name,
                'slug': genre.slug,
                'url': build_url(updated),
                'is_active': genre.slug in selected_set,
            })

        reset_url = build_url([])
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
