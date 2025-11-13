from django.contrib import admin
from .models import Category, Genre, Product, ProductImage, Banner, ProductReview


class BannerAdmin(admin.ModelAdmin):
	list_display = ('title', 'image', 'link', 'is_active', 'created_at', 'updated_at')
	list_filter = ('is_active', 'title')
	search_fields = ('title', 'link')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('author_name', 'rating', 'text', 'created_at')
    can_delete = False
    show_change_link = False
    

class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'genre', 'condition', 'collection', 'price', 'in_stock', 'is_published', 'updated_at', 'slug', 'authors', 'publisher')
	list_filter = ('category', 'genre', 'condition', 'is_published', 'in_stock', 'collection')
	search_fields = ('name', 'authors', 'publisher', 'isbn')
	prepopulated_fields = {'slug': ('name',)}
	autocomplete_fields = ('category', 'genre')
	inlines = [ProductImageInline, ProductReviewInline]


class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	search_fields = ('name',)
	prepopulated_fields = {'slug': ('name',)}


class GenreAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'position', 'slug', 'image')
	list_filter = ('category',)
	search_fields = ('name',)
	prepopulated_fields = {'slug': ('name',)}
 

admin.site.register(Category, CategoryAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Banner, BannerAdmin)
