from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class ProductConditionChoices(models.TextChoices):
    GIFT = 'gift', 'Подарочное'
    EXCELLENT = 'excellent', 'Отличное'
    GOOD = 'good', 'Хорошее'
    FAIR = 'fair', 'Удовлетворительное'


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
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
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
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

    def __str__(self):
        return self.name
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/extra')
    alt_text = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Изображение {self.product.name} позиция {self.position}"
    
    
