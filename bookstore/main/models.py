from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from .enums import ProductConditionChoices, ProductCollections


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Genre(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='genres',
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    position = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='genres/', blank=True, null=True)

    class Meta:
        unique_together = ('category', 'slug')
        ordering = ('position', 'name')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    external_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True,
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    authors = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    main_image = models.ImageField(upload_to='products/main')
    isbn = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    condition = models.CharField(
        max_length=16,
        choices=ProductConditionChoices.choices,
        default=ProductConditionChoices.EXCELLENT,
    )
    collection = models.CharField(
        max_length=16,
        choices=ProductCollections.choices,
        null=True,
        blank=True,
    )
    price = models.DecimalField(max_digits=10, decimal_places=0)
    old_price = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    currency = models.CharField(max_length=3, default='RUB')
    in_stock = models.BooleanField(default=True)
    stock_qty = models.PositiveIntegerField(default=1)
    weight_g = models.PositiveIntegerField(default=300)
    is_published = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.genre:
            self.category = self.genre.category
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    def _format_amount(self, amount):
        """
        Приводит числовое значение к строке с символом валюты и пробелами между разрядами.
        """
        symbols = {
            'RUB': '₽',
            'USD': '$',
            'EUR': '€',
        }
        symbol = symbols.get(self.currency.upper(), self.currency)
        return f"{int(amount):,}".replace(',', ' ') + f" {symbol}"

    def formatted_price(self):
        return self._format_amount(self.price)
    
    def formatted_old_price(self):
        if self.old_price is None:
            return ''
        return self._format_amount(self.old_price)

    def __str__(self):
        return self.name


class ProductReview(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    author_name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(default=5)
    text = models.TextField()
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.author_name}: {self.rating}'
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/extra')
    alt_text = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Изображение {self.product.name} позиция {self.position}"


class BookPurchaseRequest(models.Model):
    email = models.EmailField()
    phone = models.CharField(max_length=64)
    book_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"Заявка {self.email} от {self.created_at:%d.%m.%Y}"


class BookPurchasePhoto(models.Model):
    request = models.ForeignKey(
        BookPurchaseRequest,
        on_delete=models.CASCADE,
        related_name='photos',
    )
    image = models.ImageField(upload_to='purchase_requests/photos')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Фото заявки #{self.request_id}"


class Banner(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='banners/main')
    link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class DeepSeekPrompt(models.Model):
    text = models.TextField(default='Ты — литературный критик. Сформулируй по-русски выразительную рецензию из 2–3 абзацев, '
            'делай акцент на идеях и стиле произведения. Не пересказывай сюжет подробно и уложись примерно в 1200 символов.\n')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
