from django.contrib import admin
from django.utils.html import format_html_join
from .models import (
    Category,
    Genre,
    Product,
    Banner,
    ProductReview,
    DeepSeekPrompt,
    BookPurchaseRequest,
    BookPurchasePhoto,
)


class BannerAdmin(admin.ModelAdmin):
    list_display = (
        'title_display',
        'image_display',
        'link_display',
        'is_active_display',
        'created_at_display',
        'updated_at_display',
    )
    list_filter = ('is_active', 'title')
    search_fields = ('title', 'link')

    @admin.display(description='Заголовок', ordering='title')
    def title_display(self, obj):
        return obj.title

    @admin.display(description='Изображение', ordering='image')
    def image_display(self, obj):
        return obj.image

    @admin.display(description='Ссылка', ordering='link')
    def link_display(self, obj):
        return obj.link

    @admin.display(description='Активен', boolean=True, ordering='is_active')
    def is_active_display(self, obj):
        return obj.is_active

    @admin.display(description='Создан', ordering='created_at')
    def created_at_display(self, obj):
        return obj.created_at

    @admin.display(description='Обновлен', ordering='updated_at')
    def updated_at_display(self, obj):
        return obj.updated_at

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        labels = {
            'title': 'Заголовок',
            'image': 'Изображение',
            'link': 'Ссылка',
            'is_active': 'Активен',
            'created_at': 'Создан',
            'updated_at': 'Обновлен',
        }
        for field_name, label in labels.items():
            if field_name in form.base_fields:
                form.base_fields[field_name].label = label
        return form


class BookPurchasePhotoInline(admin.TabularInline):
    model = BookPurchasePhoto
    extra = 0
    readonly_fields = ('image', 'uploaded_at')


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('author_name', 'rating', 'text', 'created_at')
    can_delete = False
    show_change_link = False
    

class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name_display',
        'category_display',
        'genre_display',
        'condition_display',
        'collection_display',
        'price_display',
        'in_stock_display',
        'is_published_display',
        'updated_at_display',
        'slug_display',
        'authors_display',
        'publisher_display',
    )
    list_filter = ('category', 'genre', 'condition', 'is_published', 'in_stock', 'collection')
    search_fields = ('name', 'authors', 'publisher', 'isbn')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('category', 'genre')
    inlines = [ProductReviewInline]
    readonly_fields = ('external_images_preview',)

    def external_images_preview(self, obj):
        images = obj.external_images or []
        urls = []
        if isinstance(images, list):
            for image in images:
                if not isinstance(image, dict):
                    continue
                url = image.get('url')
                if url:
                    urls.append(url)
        if not urls and obj.external_image_url:
            urls.append(obj.external_image_url)
        if not urls:
            return '—'
        return format_html_join(
            '',
            '<img src="{}" style="height: 80px; margin: 2px; border: 1px solid #ddd; border-radius: 4px;" />',
            ((url,) for url in urls),
        )

    external_images_preview.short_description = 'ERP изображения'

    @admin.display(description='Название', ordering='name')
    def name_display(self, obj):
        return obj.name

    @admin.display(description='Категория', ordering='category')
    def category_display(self, obj):
        return obj.category

    @admin.display(description='Жанр', ordering='genre')
    def genre_display(self, obj):
        return obj.genre

    @admin.display(description='Состояние', ordering='condition')
    def condition_display(self, obj):
        return obj.get_condition_display()

    @admin.display(description='Коллекция', ordering='collection')
    def collection_display(self, obj):
        if not obj.collection:
            return '—'
        return obj.get_collection_display()

    @admin.display(description='Цена', ordering='price')
    def price_display(self, obj):
        return obj.price

    @admin.display(description='В наличии', boolean=True, ordering='in_stock')
    def in_stock_display(self, obj):
        return obj.in_stock

    @admin.display(description='Опубликован', boolean=True, ordering='is_published')
    def is_published_display(self, obj):
        return obj.is_published

    @admin.display(description='Обновлен', ordering='updated_at')
    def updated_at_display(self, obj):
        return obj.updated_at

    @admin.display(description='Слаг', ordering='slug')
    def slug_display(self, obj):
        return obj.slug

    @admin.display(description='Автор', ordering='authors')
    def authors_display(self, obj):
        return obj.authors

    @admin.display(description='Издательство', ordering='publisher')
    def publisher_display(self, obj):
        return obj.publisher

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        labels = {
            'name': 'Название',
            'category': 'Категория',
            'genre': 'Жанр',
            'condition': 'Состояние',
            'collection': 'Коллекция',
            'price': 'Цена',
            'old_price': 'Старая цена',
            'in_stock': 'В наличии',
            'stock_qty': 'Остаток',
            'is_published': 'Опубликован',
            'slug': 'Слаг',
            'authors': 'Автор',
            'publisher': 'Издательство',
            'description': 'Описание',
            'main_image': 'Главное изображение',
            'external_image_url': 'Внешнее изображение (URL)',
            'external_images': 'Внешние изображения',
            'updated_at': 'Обновлен',
            'created_at': 'Создан',
        }
        for field_name, label in labels.items():
            if field_name in form.base_fields:
                form.base_fields[field_name].label = label
        return form


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class GenreAdmin(admin.ModelAdmin):
    list_display = ('name_display', 'category_display', 'position_display', 'slug_display', 'image_display')
    list_filter = ('category',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Название', ordering='name')
    def name_display(self, obj):
        return obj.name

    @admin.display(description='Категория', ordering='category')
    def category_display(self, obj):
        return obj.category

    @admin.display(description='Позиция', ordering='position')
    def position_display(self, obj):
        return obj.position

    @admin.display(description='Слаг', ordering='slug')
    def slug_display(self, obj):
        return obj.slug

    @admin.display(description='Изображение', ordering='image')
    def image_display(self, obj):
        return obj.image

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        labels = {
            'name': 'Название',
            'category': 'Категория',
            'position': 'Позиция',
            'slug': 'Слаг',
            'image': 'Изображение',
        }
        for field_name, label in labels.items():
            if field_name in form.base_fields:
                form.base_fields[field_name].label = label
        return form


class DeepSeekPromptAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'created_at', 'updated_at')

    def short_text(self, obj):
        return (obj.text or '').strip()[:80]

    short_text.short_description = 'Текст'


@admin.register(BookPurchaseRequest)
class BookPurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'created_at')
    readonly_fields = ('email', 'phone', 'book_description', 'created_at', 'updated_at')
    search_fields = ('email', 'phone', 'book_description')
    inlines = (BookPurchasePhotoInline,)
    ordering = ('-created_at',)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register(DeepSeekPrompt, DeepSeekPromptAdmin)
