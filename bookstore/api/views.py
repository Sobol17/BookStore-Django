import json
import logging
import uuid
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from common.slugs import slugify_translit
from django.views.decorators.http import require_http_methods

from main.models import Category, Product
from orders.models import Order

logger = logging.getLogger(__name__)

BATCH_LIMIT = 100
ORDER_STATUS_MAPPING = {
    'new': 'pending',
    'pending': 'pending',
    'processing': 'processing',
    'shipped': 'shipped',
    'delivered': 'delivered',
    'cancelled': 'cancelled',
}


def error_response(code: str, message: str, *, details=None, status: int = 400) -> JsonResponse:
    payload = {
        'code': code,
        'message': message,
    }
    if details is not None:
        payload['details'] = details
    return JsonResponse(payload, status=status)


def _get_bearer_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ', 1)[1].strip()


def require_api_key(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        api_key = settings.INTERNET_SHOP_API_KEY
        if not api_key:
            logger.error('INTERNET_SHOP_API_KEY is not configured')
            return error_response('config_error', 'API key is not configured', status=500)
        token = _get_bearer_token(request)
        if not token:
            return error_response('unauthorized', 'Missing Bearer token', status=401)
        if token != api_key:
            return error_response('unauthorized', 'Invalid API key', status=401)
        return view_func(request, *args, **kwargs)

    return wrapped


def parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        raise ValueError('Invalid JSON payload')


def clean_identifier(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def ensure_category(category_name: str | None):
    if not category_name:
        return None
    category_name = category_name.strip()
    if not category_name:
        return None
    slug = slugify_translit(category_name)
    category, _ = Category.objects.get_or_create(
        name=category_name,
        defaults={'slug': slug},
    )
    return category


def generate_unique_slug(base_value: str | None):
    base_slug = slugify_translit(base_value) or str(uuid.uuid4())
    slug_candidate = base_slug
    counter = 1
    while Product.objects.filter(slug=slug_candidate).exists():
        counter += 1
        slug_candidate = f'{base_slug}-{counter}'
    return slug_candidate


def parse_decimal(value, field_name: str):
    if value is None:
        raise ValueError(f'{field_name} is required')
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValueError(f'{field_name} must be a number')


def parse_int(value, field_name: str):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f'{field_name} must be an integer')


def sanitize_dimensions(dimensions):
    if not isinstance(dimensions, (list, tuple)):
        return []
    cleaned = []
    for entry in dimensions:
        try:
            cleaned.append(float(entry))
        except (TypeError, ValueError):
            continue
    return cleaned[:3]


def sanitize_images(images):
    if not isinstance(images, list):
        return [], ''
    cleaned = []
    for image in images:
        if not isinstance(image, dict):
            continue
        url = clean_identifier(image.get('url'))
        if not url:
            continue
        position = image.get('position')
        try:
            position = int(position)
        except (TypeError, ValueError):
            position = 0
        cleaned.append({'url': url, 'position': position})
    cleaned.sort(key=lambda item: item['position'])
    main_url = cleaned[0]['url'] if cleaned else ''
    return cleaned, main_url


def sanitize_attributes(attrs):
    if isinstance(attrs, dict):
        return attrs
    return {}


def find_product(payload):
    product = None
    shop_product_id = clean_identifier(payload.get('shop_product_id'))
    if shop_product_id:
        try:
            product = Product.objects.get(pk=int(shop_product_id))
        except (Product.DoesNotExist, ValueError):
            raise ValueError(f'Product with shop_product_id={shop_product_id} was not found')
    if product:
        return product, False
    sku = clean_identifier(payload.get('sku'))
    if sku:
        product = Product.objects.filter(sku=sku).first()
    if product:
        return product, False
    offer_id = clean_identifier(payload.get('offer_id'))
    if offer_id:
        product = Product.objects.filter(offer_id=offer_id).first()
    if product:
        return product, False
    erp_product_id = clean_identifier(payload.get('product_id'))
    if erp_product_id:
        product = Product.objects.filter(erp_product_id=erp_product_id).first()
    if product:
        return product, False
    return None, True


def upsert_single_product(payload):
    if not isinstance(payload, dict):
        raise ValueError('Each product entry must be an object')
    product, is_new = find_product(payload)
    if is_new:
        sku = clean_identifier(payload.get('sku'))
        if not sku:
            raise ValueError('Field sku is required for new products')
        name = clean_identifier(payload.get('name'))
        if not name:
            raise ValueError('Field name is required for new products')
        slug_value = payload.get('slug') or sku or name
        product = Product(
            slug=generate_unique_slug(slug_value),
            stock_qty=0,
            in_stock=False,
        )
        product.name = name
    name = clean_identifier(payload.get('name'))
    if name:
        product.name = name
    description = payload.get('description')
    if description is not None:
        product.description = description
    isbn = clean_identifier(payload.get('isbn'))
    if isbn is not None:
        product.isbn = isbn
    barcode = clean_identifier(payload.get('barcode'))
    if barcode is not None:
        product.barcode = barcode
    offer_id = clean_identifier(payload.get('offer_id'))
    if offer_id:
        product.offer_id = offer_id
    product_id = clean_identifier(payload.get('product_id'))
    if product_id:
        product.erp_product_id = product_id
    sku = clean_identifier(payload.get('sku'))
    if sku:
        product.sku = sku
    category_name = payload.get('category')
    category = ensure_category(category_name)
    if category:
        product.category = category
    price = payload.get('price')
    if price is not None:
        product.price = parse_decimal(price, 'price')
    elif is_new:
        raise ValueError('Field price is required for new products')
    currency = clean_identifier(payload.get('currency'))
    if currency:
        product.currency = currency.upper()[:3]
    vat = payload.get('vat')
    if vat is not None:
        vat_value = parse_int(vat, 'vat')
        product.vat_rate = vat_value if vat_value is not None else None
    weight = payload.get('weight_g')
    if weight is not None:
        weight_value = parse_int(weight, 'weight_g')
        if weight_value is not None and weight_value > 0:
            product.weight_g = weight_value
    if 'dimensions_cm' in payload:
        product.dimensions_cm = sanitize_dimensions(payload.get('dimensions_cm'))
    if 'attributes' in payload:
        product.attributes = sanitize_attributes(payload.get('attributes'))
    if 'images' in payload:
        images, main_url = sanitize_images(payload.get('images'))
        product.external_images = images
        product.external_image_url = main_url
    published = payload.get('is_published')
    if isinstance(published, bool):
        product.is_published = published
    old_price = payload.get('old_price')
    if old_price is not None:
        product.old_price = parse_decimal(old_price, 'old_price')
    product.full_clean()
    product.save()
    status = 'created' if is_new else 'updated'
    return product, status


@require_http_methods(['POST'])
@require_api_key
def products_bulk_upsert(request):
    try:
        payload = parse_json_body(request)
    except ValueError as exc:
        return error_response('invalid_json', str(exc))
    items = payload.get('products')
    if not isinstance(items, list) or not items:
        return error_response('validation_error', 'Field "products" must be a non-empty array')
    if len(items) > BATCH_LIMIT:
        return error_response('validation_error', f'Batch size limit is {BATCH_LIMIT}')
    results = []
    errors = []
    for index, item in enumerate(items):
        try:
            product, status = upsert_single_product(item)
            results.append({
                'sku': product.sku or item.get('sku'),
                'shop_product_id': str(product.pk),
                'status': status,
            })
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception('Product upsert failed: %s', exc)
            errors.append({
                'index': index,
                'sku': item.get('sku'),
                'message': str(exc),
            })
    return JsonResponse({'results': results, 'errors': errors})


@require_http_methods(['POST'])
@require_api_key
def stocks_bulk_update(request):
    try:
        payload = parse_json_body(request)
    except ValueError as exc:
        return error_response('invalid_json', str(exc))
    warehouse_code = payload.get('warehouse_code') or settings.INTERNET_SHOP_DEFAULT_WAREHOUSE
    if warehouse_code != settings.INTERNET_SHOP_DEFAULT_WAREHOUSE:
        return error_response('validation_error', f'Unknown warehouse code "{warehouse_code}"')
    items = payload.get('items')
    if not isinstance(items, list) or not items:
        return error_response('validation_error', 'Field "items" must be a non-empty array')
    results = []
    errors = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append({'index': index, 'message': 'Each item must be an object'})
            continue
        sku = clean_identifier(item.get('sku'))
        quantity = item.get('quantity')
        if not sku:
            errors.append({'index': index, 'message': 'Field sku is required'})
            continue
        try:
            qty_value = int(quantity)
        except (TypeError, ValueError):
            errors.append({'index': index, 'sku': sku, 'message': 'Field quantity must be an integer'})
            continue
        product = Product.objects.filter(sku=sku).first()
        if not product:
            errors.append({'index': index, 'sku': sku, 'message': 'Product not found'})
            continue
        product.stock_qty = max(qty_value, 0)
        product.in_stock = qty_value > 0
        product.save(update_fields=['stock_qty', 'in_stock', 'updated_at'])
        results.append({'sku': sku, 'quantity': product.stock_qty, 'status': 'updated'})
    return JsonResponse({'warehouse_code': warehouse_code, 'results': results, 'errors': errors})


def _filter_orders(request):
    status_param = request.GET.get('status')
    status_value = None
    if status_param:
        status_value = ORDER_STATUS_MAPPING.get(status_param.lower())
        if not status_value:
            return None, error_response('validation_error', f'Unsupported status "{status_param}"')
    queryset = Order.objects.all().order_by('created_at')
    if status_value:
        queryset = queryset.filter(status=status_value)
        if status_value == 'pending':
            queryset = queryset.filter(erp_acknowledged_at__isnull=True)
    else:
        queryset = queryset.filter(erp_acknowledged_at__isnull=True)
    updated_from_raw = request.GET.get('updated_from')
    if updated_from_raw:
        parsed = parse_datetime(updated_from_raw)
        if not parsed:
            return None, error_response('validation_error', 'updated_from must be ISO 8601 datetime')
        queryset = queryset.filter(updated_at__gte=parsed)
    return queryset, None


def serialize_order(order: Order):
    items = []
    for item in order.items.select_related('product'):
        product = item.product
        items.append({
            'sku': product.sku or product.offer_id or str(product.id),
            'name': product.name,
            'qty': item.quantity,
            'price': float(item.price),
        })
    customer_name = ' '.join(filter(None, [order.first_name, order.last_name]))
    return {
        'shop_order_id': str(order.pk),
        'status': order.status,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
        'customer': {
            'name': customer_name.strip() or order.first_name,
            'phone': order.phone,
            'email': order.email,
        },
        'items': items,
        'delivery': {
            'method': 'standard',
            'address': {
                'full': order.formatted_address,
            }
        },
        'payments': {
            'total': float(order.total_price),
            'currency': 'RUB',
        }
    }


@require_http_methods(['GET'])
@require_api_key
def orders_list(request):
    queryset, error = _filter_orders(request)
    if error:
        return error
    page_number = request.GET.get('page') or 1
    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        return error_response('validation_error', 'page must be an integer')
    paginator = Paginator(queryset, settings.INTERNET_SHOP_PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    data = [serialize_order(order) for order in page_obj]
    next_page = page_obj.next_page_number() if page_obj.has_next() else None
    return JsonResponse({'orders': data, 'next_page': next_page})


def _get_order_or_404(shop_order_id: str):
    try:
        order_id = int(shop_order_id)
    except (TypeError, ValueError):
        return None
    return Order.objects.filter(pk=order_id).first()


@require_http_methods(['POST'])
@require_api_key
def order_acknowledge(request, shop_order_id: str):
    order = _get_order_or_404(shop_order_id)
    if not order:
        return error_response('not_found', 'Order not found', status=404)
    try:
        payload = parse_json_body(request)
    except ValueError as exc:
        return error_response('invalid_json', str(exc))
    order.erp_acknowledged_at = timezone.now()
    update_fields = ['erp_acknowledged_at', 'updated_at']
    if 'external_id' in payload:
        order.erp_external_id = clean_identifier(payload.get('external_id')) or ''
        update_fields.append('erp_external_id')
    if 'status' in payload:
        ack_status = clean_identifier(payload.get('status'))
        if ack_status:
            order.erp_status = ack_status
            update_fields.append('erp_status')
    order.save(update_fields=update_fields)
    return JsonResponse({'shop_order_id': str(order.pk), 'status': 'acknowledged'})


@require_http_methods(['POST'])
@require_api_key
def order_status_update(request, shop_order_id: str):
    order = _get_order_or_404(shop_order_id)
    if not order:
        return error_response('not_found', 'Order not found', status=404)
    try:
        payload = parse_json_body(request)
    except ValueError as exc:
        return error_response('invalid_json', str(exc))
    update_fields = ['updated_at']
    status_value = payload.get('status')
    if status_value is not None:
        mapped_status = ORDER_STATUS_MAPPING.get(str(status_value).lower())
        if not mapped_status:
            return error_response('validation_error', f'Unsupported status "{status_value}"')
        order.status = mapped_status
        update_fields.append('status')
    if 'comment' in payload:
        order.erp_status_comment = clean_identifier(payload.get('comment')) or ''
        update_fields.append('erp_status_comment')
    external_status_value = payload.get('external_status')
    if external_status_value is not None or status_value is not None:
        chosen = clean_identifier(external_status_value)
        if not chosen and status_value is not None:
            chosen = str(status_value)
        order.erp_status = chosen or ''
        update_fields.append('erp_status')
    order.erp_status_updated_at = timezone.now()
    update_fields.append('erp_status_updated_at')
    order.save(update_fields=update_fields)
    return JsonResponse({'shop_order_id': str(order.pk), 'status': order.status})
