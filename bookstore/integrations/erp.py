import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib import error, request
from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from common.slugs import slugify_translit

from main.models import Category, Genre, Product, ErpProductSyncState
from orders.models import Order

logger = logging.getLogger(__name__)


class ErpConfigurationError(RuntimeError):
    """Raised when ERP API settings are missing."""


class ErpAPIError(RuntimeError):
    """Raised when ERP API responds with an error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


@dataclass
class ErpClient:
    base_url: str
    api_key: str
    timeout: int = 15

    def __post_init__(self) -> None:
        if not self.base_url:
            raise ErpConfigurationError('ERP base URL is not configured.')
        if not self.api_key:
            raise ErpConfigurationError('ERP API key is not configured.')
        if not self.base_url.endswith('/'):
            self.base_url = f'{self.base_url}/'

    def list_products(
        self,
        *,
        updated_since: Optional[str] = None,
        page_size: int = 50,
    ) -> Iterable[List[Dict[str, Any]]]:
        page = 1
        while True:
            params: Dict[str, Any] = {
                'page': page,
                'page_size': min(max(page_size, 1), 1000),
                'is_active': 'true',
                'in_stock': 'true',
            }
            if updated_since:
                params['updated_since'] = updated_since
            payload = self._request('GET', 'products/', params=params)
            results = payload.get('results') or []
            if not isinstance(results, list):
                raise ErpAPIError('ERP API returned invalid products payload.')
            yield results
            if not payload.get('next'):
                break
            page += 1

    def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request('POST', 'orders/', payload=payload)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = urljoin(self.base_url, path)
        if params:
            query = urlencode(params)
            url = f'{url}?{query}'
        data = None
        if payload is not None:
            data = json.dumps(payload).encode('utf-8')
        req = request.Request(url, data=data, method=method)
        req.add_header('Authorization', f'Api-Key {self.api_key}')
        req.add_header('Accept', 'application/json')
        if payload is not None:
            req.add_header('Content-Type', 'application/json')
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset() or 'utf-8'
                body = response.read().decode(charset)
        except error.HTTPError as exc:
            detail = _read_error_body(exc)
            logger.warning('ERP API responded with %s for %s %s: %s', exc.code, method, url, detail or 'no body')
            raise ErpAPIError(
                'ERP API responded with an error.',
                status_code=exc.code,
                response_body=detail,
            ) from exc
        except error.URLError as exc:
            logger.error('ERP API connection error: %s', exc.reason)
            raise ErpAPIError('Unable to reach ERP API.') from exc
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            logger.error('ERP API returned invalid JSON: %s', exc)
            raise ErpAPIError('Unable to parse ERP API response.') from exc


def get_erp_client() -> Optional[ErpClient]:
    if not getattr(settings, 'ERP_INTEGRATION_ENABLED', True):
        return None
    api_key = getattr(settings, 'ERP_API_KEY', '') or getattr(settings, 'INTERNET_SHOP_API_KEY', '')
    if not api_key:
        logger.warning('ERP integration is enabled but API key is missing.')
        return None
    base_url = getattr(settings, 'ERP_API_BASE_URL', '')
    timeout = int(getattr(settings, 'ERP_API_TIMEOUT', 15))
    return ErpClient(base_url=base_url, api_key=api_key, timeout=timeout)


def require_erp_client() -> ErpClient:
    client = get_erp_client()
    if not client:
        raise ErpConfigurationError('ERP integration is disabled or not configured.')
    return client


def send_order_to_erp(order: Order) -> Optional[Dict[str, Any]]:
    if order.erp_acknowledged_at:
        return None
    client = get_erp_client()
    if not client:
        return None
    payload = build_order_payload(order)
    response = client.create_order(payload)
    _apply_order_response(order, response)
    return response


def push_order_to_erp(order_id: int) -> None:
    try:
        order = (
            Order.objects.select_related('user')
            .prefetch_related('items__product')
            .get(pk=order_id)
        )
    except Order.DoesNotExist:
        logger.warning('ERP push skipped: order %s not found.', order_id)
        return
    try:
        send_order_to_erp(order)
    except Exception:
        logger.exception('ERP push failed for order %s.', order_id)


def build_order_payload(order: Order) -> Dict[str, Any]:
    items_payload: List[Dict[str, Any]] = []
    for item in order.items.select_related('product'):
        product = item.product
        product_id = _normalize_product_id(product.erp_product_id)
        sku = _clean_text(product.sku)
        if not product_id and not sku:
            raise ValueError(f'Order {order.pk} item {item.pk} has no sku or ERP product id.')
        price_value = _format_decimal(item.price)
        item_payload: Dict[str, Any] = {
            'quantity': item.quantity,
            'price': price_value,
        }
        if product_id:
            item_payload['product_id'] = product_id
        else:
            item_payload['sku'] = sku
        items_payload.append(item_payload)
    if not items_payload:
        raise ValueError(f'Order {order.pk} has no items to send.')
    currency = _clean_text(getattr(settings, 'ERP_DEFAULT_CURRENCY', 'RUB')) or 'RUB'
    customer_name = ' '.join(filter(None, [order.first_name, order.last_name])).strip()
    city = _clean_text(order.city) or ''
    country = _clean_text(getattr(settings, 'ERP_DEFAULT_COUNTRY', 'Россия')) or 'Россия'
    return {
        'external_order_id': str(order.pk),
        'currency': currency,
        'customer': {
            'name': customer_name or (_clean_text(order.first_name) or ''),
            'phone': _clean_text(order.phone) or '',
            'email': _clean_text(order.email) or '',
        },
        'shipping_address': {
            'address': _clean_text(order.formatted_address) or '',
            'city': city,
            'region': city,
            'postal_code': _clean_text(order.postal_code) or '',
            'country': country,
        },
        'items': items_payload,
    }


def _apply_order_response(order: Order, response: Dict[str, Any]) -> None:
    update_fields: List[str] = ['erp_acknowledged_at', 'updated_at']
    order.erp_acknowledged_at = timezone.now()
    erp_order_id = response.get('order_id')
    if erp_order_id is not None:
        order.erp_external_id = str(erp_order_id)
        update_fields.append('erp_external_id')
    status = response.get('status')
    if status:
        order.erp_status = str(status)
        update_fields.append('erp_status')
    order.save(update_fields=update_fields)


def sync_erp_products(
    *,
    updated_since: Optional[str | datetime] = None,
    page_size: Optional[int] = None,
    dry_run: bool = False,
    limit: Optional[int] = None,
    read_state: bool = True,
    write_state: bool = True,
) -> Dict[str, int]:
    client = require_erp_client()
    state: Optional[ErpProductSyncState] = None
    updated_since_value = updated_since
    if updated_since_value is None and read_state:
        state = ErpProductSyncState.objects.first()
        if state and state.last_synced_at:
            updated_since_value = state.last_synced_at
    updated_since_param = _format_updated_since(updated_since_value)
    page_size = page_size or getattr(settings, 'ERP_PRODUCTS_PAGE_SIZE', 50)

    stats = {
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
    }
    processed = 0
    max_updated_at: Optional[datetime] = None

    for page_items in client.list_products(updated_since=updated_since_param, page_size=page_size):
        for payload in page_items:
            if limit and processed >= limit:
                break
            try:
                _, status, updated_at = upsert_product_from_erp(payload, dry_run=dry_run)
                stats[status] += 1
                if updated_at and (max_updated_at is None or updated_at > max_updated_at):
                    max_updated_at = updated_at
            except Exception:
                stats['errors'] += 1
                logger.exception('ERP product sync failed for payload: %s', payload)
            processed += 1
        if limit and processed >= limit:
            break

    if not dry_run and write_state:
        if not state:
            state = ErpProductSyncState.objects.create()
        if max_updated_at:
            state.last_synced_at = max_updated_at
        elif updated_since_value is None:
            state.last_synced_at = timezone.now()
        state.save(update_fields=['last_synced_at', 'updated_at'])

    return stats


def upsert_product_from_erp(
    payload: Dict[str, Any],
    *,
    dry_run: bool = False,
) -> Tuple[Optional[Product], str, Optional[datetime]]:
    if not isinstance(payload, dict):
        raise ValueError('ERP product payload must be an object.')

    erp_product_id = _clean_text(payload.get('id'))
    if not erp_product_id:
        raise ValueError('ERP product id is missing.')

    sku = _clean_text(payload.get('sku'))
    offer_id = _clean_text(payload.get('offer_id'))
    product = Product.objects.filter(erp_product_id=erp_product_id).first()
    if not product:
        product = Product.objects.filter(external_id=erp_product_id).first()
    if not product and sku:
        product = Product.objects.filter(sku=sku).first()
    if not product and offer_id:
        product = Product.objects.filter(offer_id=offer_id).first()

    is_new = product is None
    if is_new:
        name = _clean_text(payload.get('name'))
        if not name:
            raise ValueError('ERP product name is required for new products.')
        slug_source = _pick_slug_source(payload, name, erp_product_id, sku, offer_id)
        product = Product(
            name=name,
            slug=_generate_unique_slug(slug_source),
            stock_qty=0,
            in_stock=False,
        )

    name = _clean_text(payload.get('name'))
    if name:
        product.name = name
    if 'description' in payload:
        product.description = payload.get('description') or ''

    if sku:
        product.sku = sku
    if offer_id:
        product.offer_id = offer_id
    product.erp_product_id = erp_product_id

    price_value, currency = _extract_price(payload.get('prices'))
    if price_value is None:
        if is_new:
            raise ValueError('ERP product price is required for new products.')
    else:
        product.price = price_value
    if currency:
        product.currency = currency

    is_visible = payload.get('is_visible')
    archived = payload.get('archived')
    if isinstance(is_visible, bool):
        product.is_published = is_visible and not bool(archived)

    if 'stock' in payload:
        stock_qty, in_stock = _extract_stock(payload.get('stock'))
        if stock_qty is not None:
            product.stock_qty = stock_qty
            product.in_stock = in_stock

    if 'images' in payload:
        images, main_url = _extract_images(payload.get('images'))
        product.external_images = images
        product.external_image_url = main_url

    if 'categories' in payload:
        category_name, genre_name = _resolve_category_genre(payload.get('categories'))
        if category_name:
            category = _ensure_category(category_name)
            product.category = category
            if genre_name:
                genre = _ensure_genre(category, genre_name)
                product.genre = genre
            else:
                product.genre = None

    book_author = _extract_book_author(payload)
    if book_author:
        product.authors = book_author

    book_genre_name = _extract_book_genre(payload)
    if book_genre_name:
        category = product.category
        if not category:
            category = _ensure_category('Книги')
            product.category = category
        product.genre = _ensure_genre(category, book_genre_name)

    vinyl_details = _extract_vinyl_details(payload)
    if vinyl_details is not None:
        _apply_vinyl_details(product, payload, vinyl_details)

    postcard_details = _extract_postcard_details(payload)
    if postcard_details is not None:
        _apply_postcard_details(product, payload, postcard_details)

    if name and _should_refresh_slug(product.slug, erp_product_id, sku, offer_id):
        product.slug = _generate_unique_slug(name)

    if dry_run:
        return product, 'created' if is_new else 'updated', _parse_updated_at(payload)

    product.save()
    return product, 'created' if is_new else 'updated', _parse_updated_at(payload)


def _extract_price(prices: Any) -> Tuple[Optional[Decimal], Optional[str]]:
    if not isinstance(prices, list) or not prices:
        return None, None
    chosen = None
    for price in prices:
        if not isinstance(price, dict):
            continue
        if price.get('marketplace') == 'internet_shop':
            chosen = price
            break
        if not chosen:
            chosen = price
    if not chosen:
        return None, None
    raw_price = chosen.get('price')
    if raw_price is None:
        return None, None
    try:
        value = Decimal(str(raw_price))
    except (InvalidOperation, TypeError):
        raise ValueError('ERP price is not a valid number.')
    currency = _clean_text(chosen.get('currency_code'))
    return value, currency


def _extract_stock(stock: Any) -> Tuple[Optional[int], bool]:
    if not isinstance(stock, dict):
        return None, False
    total = stock.get('total')
    reserved = stock.get('reserved')
    try:
        total_value = int(total)
    except (TypeError, ValueError):
        return None, False
    try:
        reserved_value = int(reserved)
    except (TypeError, ValueError):
        reserved_value = 0
    available = max(total_value - reserved_value, 0)
    return available, available > 0


def _extract_images(images: Any) -> Tuple[List[Dict[str, Any]], str]:
    if not isinstance(images, list):
        return [], ''
    cleaned: List[Dict[str, Any]] = []
    main_url = ''
    for image in images:
        if not isinstance(image, dict):
            continue
        url = _clean_text(image.get('url'))
        if not url:
            continue
        position = image.get('order', image.get('position', 0))
        try:
            position_value = int(position)
        except (TypeError, ValueError):
            position_value = 0
        if not main_url and image.get('is_main'):
            main_url = url
        cleaned.append({'url': url, 'position': position_value})
    cleaned.sort(key=lambda item: item.get('position', 0))
    if not main_url and cleaned:
        main_url = cleaned[0]['url']
    return cleaned, main_url


def _resolve_category_genre(categories: Any) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(categories, list) or not categories:
        return None, None
    by_id = {}
    parents = set()
    for entry in categories:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get('id')
        if entry_id is None:
            continue
        by_id[entry_id] = entry
        parent_id = entry.get('parent_id')
        if parent_id is not None:
            parents.add(parent_id)
    leaves = [item for item in by_id.values() if item.get('id') not in parents]
    chosen = leaves[0] if leaves else next(iter(by_id.values()), None)
    if not chosen:
        return None, None
    parent = by_id.get(chosen.get('parent_id'))
    if parent:
        return _clean_text(parent.get('name')), _clean_text(chosen.get('name'))
    return _clean_text(chosen.get('name')), None


def _extract_book_author(payload: Dict[str, Any]) -> Optional[str]:
    details = payload.get('book_details')
    if isinstance(details, dict):
        author = _clean_text(details.get('author')) or _clean_text(details.get('authors'))
        if author:
            return author

    return _extract_additional_parameter(
        payload.get('additional_parameters'),
        {'автор', 'авторы'},
    )


def _extract_book_genre(payload: Dict[str, Any]) -> Optional[str]:
    return _extract_additional_parameter(
        payload.get('additional_parameters'),
        {'жанры товара'},
    )


def _extract_additional_parameter(
    parameters: Any,
    names: set[str],
) -> Optional[str]:
    if not isinstance(parameters, list):
        return None
    normalized_names = {item.casefold() for item in names}

    for parameter in parameters:
        if not isinstance(parameter, dict):
            continue
        parameter_name = _clean_text(
            parameter.get('name')
            or parameter.get('title')
            or parameter.get('parameter')
            or parameter.get('label')
        )
        if not parameter_name or parameter_name.casefold() not in normalized_names:
            continue

        value = _extract_additional_parameter_value(parameter)
        if value:
            return value
    return None


def _extract_additional_parameter_value(parameter: Dict[str, Any]) -> Optional[str]:
    direct_value = _clean_text(
        parameter.get('genre')
        or parameter.get('value')
        or parameter.get('display_value')
        or parameter.get('text')
    )
    if direct_value:
        return direct_value

    values = parameter.get('values')
    if not isinstance(values, list):
        return None

    normalized_values: List[str] = []
    for raw_value in values:
        if isinstance(raw_value, dict):
            cleaned_value = _clean_text(
                raw_value.get('value')
                or raw_value.get('name')
                or raw_value.get('title')
                or raw_value.get('text')
            )
        else:
            cleaned_value = _clean_text(raw_value)
        if cleaned_value:
            normalized_values.append(cleaned_value)

    if not normalized_values:
        return None
    return ', '.join(normalized_values)


def _extract_vinyl_details(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    details = payload.get('vinyl_details')
    if not isinstance(details, dict):
        return None
    return details


def _extract_postcard_details(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    details = payload.get('postcard_details')
    if not isinstance(details, dict):
        return None
    return details


def _apply_vinyl_details(
    product: Product,
    payload: Dict[str, Any],
    details: Dict[str, Any],
) -> None:
    vinyl_category = _ensure_category('vinyl')
    product.category = vinyl_category

    genre_name = _clean_text(details.get('genre'))
    if genre_name:
        product.genre = _ensure_genre(vinyl_category, genre_name)
    elif 'genre' in details:
        product.genre = None

    artist = _clean_text(details.get('artist'))
    if artist:
        product.authors = artist

    label = _clean_text(details.get('label'))
    if label:
        product.publisher = label

    release_year = _parse_int(details.get('release_year'))
    if release_year and release_year > 0:
        product.year = release_year

    barcode = _clean_text(payload.get('barcode')) or _clean_text(details.get('barcode'))
    if barcode:
        product.barcode = barcode


def _apply_postcard_details(
    product: Product,
    payload: Dict[str, Any],
    details: Dict[str, Any],
) -> None:
    postcards_category = _ensure_category('Открытки, марки, значки')
    product.category = postcards_category

    genre_name = _clean_text(details.get('theme')) or _clean_text(details.get('collection_type'))
    if genre_name:
        product.genre = _ensure_genre(postcards_category, genre_name)
    elif 'theme' in details or 'collection_type' in details:
        product.genre = None

    release_year = _parse_int(details.get('release_year'))
    if release_year and release_year > 0:
        product.year = release_year

    publisher = _clean_text(details.get('publisher'))
    if publisher:
        product.publisher = publisher

    if not _clean_text(payload.get('description')):
        postcard_description = _clean_text(details.get('description'))
        if postcard_description:
            product.description = postcard_description


def _ensure_category(name: str) -> Category:
    category = Category.objects.filter(name=name).first()
    if category:
        return category
    slug = _generate_unique_category_slug(name)
    return Category.objects.create(name=name, slug=slug)


def _ensure_genre(category: Category, name: str) -> Genre:
    normalized = name.strip()
    if not normalized:
        raise ValueError('Genre name is required.')
    existing = Genre.objects.filter(category=category, name__iexact=normalized).first()
    if existing:
        return existing
    slug = _generate_unique_genre_slug(category, normalized)
    return Genre.objects.create(category=category, name=normalized, slug=slug)


def _slug_max_length(model: type[models.Model]) -> int:
    field = model._meta.get_field('slug')
    return field.max_length or 50


def _format_slug_candidate(base_slug: str, counter: int, max_length: int) -> str:
    if counter <= 1:
        return base_slug[:max_length].rstrip('-')
    suffix = f'-{counter}'
    max_base_len = max_length - len(suffix)
    if max_base_len <= 0:
        return base_slug[:max_length].rstrip('-')
    base_part = base_slug[:max_base_len].rstrip('-')
    return f'{base_part}{suffix}'


def _generate_unique_slug(value: Optional[str]) -> str:
    base_slug = slugify_translit(value) or str(uuid.uuid4())
    max_length = _slug_max_length(Product)
    counter = 1
    while True:
        slug_candidate = _format_slug_candidate(base_slug, counter, max_length)
        if not Product.objects.filter(slug=slug_candidate).exists():
            return slug_candidate
        counter += 1


def _generate_unique_category_slug(value: str) -> str:
    base_slug = slugify_translit(value) or str(uuid.uuid4())
    max_length = _slug_max_length(Category)
    counter = 1
    while True:
        slug_candidate = _format_slug_candidate(base_slug, counter, max_length)
        if not Category.objects.filter(slug=slug_candidate).exists():
            return slug_candidate
        counter += 1


def _generate_unique_genre_slug(category: Category, value: str) -> str:
    base_slug = slugify_translit(value) or str(uuid.uuid4())
    max_length = _slug_max_length(Genre)
    counter = 1
    while True:
        slug_candidate = _format_slug_candidate(base_slug, counter, max_length)
        if not Genre.objects.filter(category=category, slug=slug_candidate).exists():
            return slug_candidate
        counter += 1


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_int(value: Any) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _pick_slug_source(
    payload: Dict[str, Any],
    name: str,
    erp_product_id: Optional[str],
    sku: Optional[str],
    offer_id: Optional[str],
) -> str:
    candidate = _clean_text(payload.get('slug'))
    if candidate and not _looks_like_code(candidate, erp_product_id, sku, offer_id):
        return candidate
    return name


def _looks_like_code(
    value: str,
    erp_product_id: Optional[str],
    sku: Optional[str],
    offer_id: Optional[str],
) -> bool:
    raw = str(value).strip()
    if not raw:
        return True
    if _looks_like_uuid(raw) or raw.isdigit():
        return True
    slug_value = slugify_translit(raw)
    for candidate in (erp_product_id, sku, offer_id):
        if not candidate:
            continue
        if slug_value == slugify_translit(str(candidate)):
            return True
    return False


def _looks_like_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return False
    return True


def _should_refresh_slug(
    slug: Optional[str],
    erp_product_id: Optional[str],
    sku: Optional[str],
    offer_id: Optional[str],
) -> bool:
    if not slug:
        return True
    if _looks_like_code(slug, erp_product_id, sku, offer_id):
        return True
    return _has_non_ascii(slug)


def _has_non_ascii(value: str) -> bool:
    try:
        value.encode('ascii')
    except UnicodeEncodeError:
        return True
    return False


def _format_decimal(value: Decimal) -> str:
    if value is None:
        raise ValueError('Decimal value is required.')
    quantized = value.quantize(Decimal('0.01'))
    return f'{quantized:.2f}'


def _normalize_product_id(value: Any) -> Optional[str | int]:
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    if cleaned.isdigit():
        return int(cleaned)
    return cleaned


def _parse_updated_at(payload: Dict[str, Any]) -> Optional[datetime]:
    raw = payload.get('updated_at')
    if not raw:
        return None
    parsed = parse_datetime(str(raw))
    if not parsed:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone=dt_timezone.utc)
    return parsed


def _format_updated_since(value: Optional[str | datetime]) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, str):
        parsed = parse_datetime(value)
        if parsed:
            value = parsed
        else:
            return value
    if isinstance(value, datetime):
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone=dt_timezone.utc)
        return value.astimezone(dt_timezone.utc).isoformat().replace('+00:00', 'Z')
    return None


def _read_error_body(exc: error.HTTPError) -> Optional[str]:
    try:
        data = exc.read()
    except Exception:
        return None
    try:
        return data.decode('utf-8')
    except Exception:
        return None
