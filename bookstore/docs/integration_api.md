# Integration API (интернет-магазин)

Базовый URL: `/api/v1/`

## API ключ

Задается через переменные окружения (рекомендуется):

- `INTERNET_SHOP_API_KEY` — обязательный ключ
- `INTERNET_SHOP_ENABLED` — опциональный флаг (`True`/`False`)

Поддерживаемые заголовки:

- `Authorization: Api-Key <KEY>`
- `X-API-KEY: <KEY>`

## GET /api/v1/products/

Возвращает товары с максимально полным набором публичных полей, включая связанные сущности и изображения.

### Query params

- `updated_since` — ISO-8601 дата или дата-время
- `page` — номер страницы
- `page_size` — максимум 100
- `is_active` — `true/false` (маппинг на `is_visible` + `archived`)
- `category_id` — фильтр по категории
- `in_stock` — `true/false` (по условию `stock.total > stock.reserved`)

### Пример

```bash
curl -H "X-API-KEY: <KEY>" \
  "https://erp.example.com/api/v1/products/?updated_since=2025-01-01T00:00:00Z&page=1&page_size=50"
```

### Пример ответа (контейнер)

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {}
  ]
}
```

### Актуальный формат элемента `results[]`

```json
{
  "images": [
    {
      "id": 863359,
      "url": "https://erp.dombb.ru/media/products/images/2025/06/product_96382_order_0.jpeg",
      "name": "product_96382_order_0.jpeg",
      "size": 594234,
      "order": 0,
      "is_main": true,
      "image_width": 1920,
      "image_height": 2560,
      "content_type": "image/jpeg"
    },
    {
      "id": 863360,
      "url": "https://erp.dombb.ru/media/products/images/2025/06/product_96382_order_1.jpeg",
      "name": "product_96382_order_1.jpeg",
      "size": 402474,
      "order": 1,
      "is_main": false,
      "image_width": 744,
      "image_height": 1200,
      "content_type": "image/jpeg"
    },
    {
      "id": 863361,
      "url": "https://erp.dombb.ru/media/products/images/2025/06/product_96382_order_2.jpeg",
      "name": "product_96382_order_2.jpeg",
      "size": 574011,
      "order": 2,
      "is_main": false,
      "image_width": 1200,
      "image_height": 957,
      "content_type": "image/jpeg"
    }
  ],
  "prices": [
    {
      "price": 240,
      "old_price": 300
    }
  ],
  "stock": {
    "id": 23380,
    "total": 1,
    "reserved": 0,
    "updated_at": "2026-02-02T18:13:52.348636+03:00"
  },
  "additional_parameters": [],
  "book_details": {
    "id": 51763,
    "isbn": "",
    "author": "",
    "publisher": "Художественная литература",
    "publication_year": 1975,
    "pages": 320,
    "format": "",
    "cover_type": "Твердый переплет",
    "weight": 325,
    "height": 18,
    "width": 130,
    "depth": 210,
    "dimension_unit": "mm",
    "weight_unit": "g",
    "description_category_id": 200001485,
    "type_id": 971818447,
    "primary_image": "https://cdn1.ozone.ru/s3/multimedia-1-3/7184340183.jpg",
    "color_image": "",
    "model_info": {
      "count": 1,
      "model_id": 449751023
    },
    "attributes": [],
    "complex_attributes": [],
    "pdf_list": [],
    "barcodes": [],
    "language": "ru",
    "age_restriction": "",
    "series": "",
    "has_color_illustrations": false,
    "translator": "",
    "circulation": null,
    "original_name": "",
    "editor": "",
    "illustrator": "",
    "paper_type": "",
    "has_glossy_paper": false,
    "book_condition": "Хорошая",
    "edition_type": "",
    "commercial_type": "",
    "has_profanity": false,
    "book_series_number": null,
    "publication_period": "",
    "direction": "",
    "edition_info": "",
    "tnved_code": "4901990000 - Прочие книги, брошюры, листовки, аналогичные печатные издания, сброшюрованные",
    "educational_period": "",
    "grade": "",
    "educational_program": "",
    "total_parts": null,
    "part_number": null
  },
  "postcard_details": null,
  "vinyl_details": null,
  "id": 96382,
  "product_id": null,
  "offer_id": "162982369",
  "name": "Золотой теленок",
  "description": "В 1931 году впервые публикуется роман И.Ильфа и Е.Петрова - \"Золотой теленок\", с тех пор романы о \"великом комбинаторе\" Остапе Бендере входят в золотой фонд российской литературы. Проходят годы, меняются поколения читателей, но истории поисков \"сокровищ\" мадам Петуховой и сложной \"операции\" по отъему денег у подпольного миллионера Корейко остаются любимыми произведениями десятков миллионов человек.<br/><br/>Дорогой читатель! Обратите внимание, что данная книга букинистическая. <br/><br/>Допустимы следы бытования: потёртости, помятые углы и дарственные надписи. <br/><br/>Эти особенности не влияют на чтение и сохранение книги в коллекции.",
  "is_visible": true,
  "archived": false,
  "is_discounted": false,
  "has_discounted_fbo": false,
  "discounted_fbo_stocks": 0,
  "is_prepayment_allowed": true,
  "placement": "",
  "currency": "RUR",
  "vat": "Без НДС",
  "unit": "шт",
  "video_url": "",
  "barcode": "",
  "quants": [
    {
      "sku": 678518222,
      "source": "sds",
      "created_at": "2022-08-18T18:15:51.595676Z",
      "quant_code": "",
      "shipment_type": "SHIPMENT_TYPE_GENERAL"
    },
    {
      "sku": 678518223,
      "source": "fbo",
      "created_at": "2022-08-18T18:15:51.607184Z",
      "quant_code": "",
      "shipment_type": "SHIPMENT_TYPE_GENERAL"
    }
  ],
  "volume_weight": "0.300",
  "created_at": "2025-04-26T15:26:06.357556+03:00",
  "updated_at": "2026-02-02T18:14:06.073822+03:00"
}
```

### Маппинг в БД при получении товаров

При получении товаров из `results[]` их необходимо размапить и сохранить в БД (модель `Product` и связанные сущности).

| Поле источника | Поле в БД | Примечание |
| --- | --- | --- |
| `id` | `Product.erp_product_id` | Основной идентификатор ERP |
| `product_id` | `Product.external_id` | Если приходит, сохраняем как внешний ID |
| `offer_id` | `Product.offer_id` | Идентификатор оффера/маркетплейса |
| `name` | `Product.name` | Обязательное поле |
| `description` | `Product.description` | HTML допускается |
| `currency` | `Product.currency` | Нормализуем до 3‑буквенного кода |
| `prices[0].price` | `Product.price` | Обязательное поле |
| `prices[0].old_price` | `Product.old_price` | Если передано |
| `is_visible`, `archived` | `Product.is_published` | `is_visible = true` и `archived = false` |
| `stock.total`, `stock.reserved` | `Product.stock_qty`, `Product.in_stock` | `available = max(total - reserved, 0)` |
| `images[].url`, `images[].order` | `Product.external_images` | Храним список `{url, position}` |
| `images[].is_main` | `Product.external_image_url` | Если нет `is_main`, берем первый по `order` |
| `book_details.author` | `Product.authors` | |
| `book_details.publisher` | `Product.publisher` | |
| `book_details.publication_year` | `Product.year` | |
| `book_details.isbn` | `Product.isbn` | |
| `barcode` или `book_details.barcodes[0]` | `Product.barcode` | Если верхний уровень пуст |
| `book_details.weight` + `weight_unit` | `Product.weight_g` | В граммах |
| `book_details.height/width/depth` + `dimension_unit` | `Product.dimensions_cm` | Конвертируем `mm` → `cm` |
| `book_details.book_condition` | `Product.condition` | Маппинг по справочнику состояния |
| `additional_parameters` | `Product.attributes` | Сохраняем как JSON при необходимости |

Прочие поля можно игнорировать либо сохранять в `Product.attributes`, если они понадобятся в витрине.

### Правило публичных полей / denylist

В ответ включаются **все поля** модели `Product`, кроме:

- технических и внутренних: `internal_notes`, `admin_comment`, `internal_barcode`, `needs_stock_update`, `is_loaded_to_ozon3`
- модерации/валидации: `has_ozon3_validation_errors`, `ozon3_validation_error_details`, `moderate_status`, `moderate_status_updated_at`, `validation_status`, `status_name`, `status_description`, `status_tooltip`
- внутренних диагностических: `visibility_details`, `errors`

Если в `Product` появится новое поле, оно автоматически появится в API, если не в denylist и не является опасным типом (binary/тяжелый JSON).

## POST /api/v1/orders/

Создает заказ идемпотентно по `external_order_id`.

### Тело запроса

```json
{
  "external_order_id": "B-100045",
  "currency": "RUB",
  "items": [
    {"product_id": 123, "quantity": 2, "price": "100.00"}
  ]
}
```

- `external_order_id` — обязателен, уникален
- `currency` — 3‑буквенный код
- `items[].product_id` или `items[].sku` — обязателен
- `items[].quantity` — > 0
- `items[].price` — decimal string

### Ответ (создан)

```json
{
  "order_id": 555,
  "external_order_id": "B-100045",
  "status": "created",
  "created": true
}
```

### Ответ (уже существует)

```json
{
  "order_id": 555,
  "external_order_id": "B-100045",
  "status": "created",
  "created": false
}
```

## Раздача медиа (публично)

Изображения должны открываться без API‑ключа.

- **Development**: Django отдает `MEDIA_URL` при `DEBUG=True` (уже включено).
- **Production**: отдавайте `MEDIA_ROOT` напрямую через Nginx/Apache (без авторизации).
  - Пример: прокиньте `/media/` на директорию из `MEDIA_ROOT`.

Установите `SITE_URL`, чтобы абсолютные ссылки формировались корректно.
