from django.contrib import admin
from .models import Category, Genre, Product, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    

class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'genre', 'condition', 'price', 'in_stock', 'is_published', 'updated_at', 'slug', 'authors', 'publisher')
	list_filter = ('category', 'genre', 'condition', 'is_published', 'in_stock')
	search_fields = ('name', 'authors', 'publisher', 'isbn')
	prepopulated_fields = {'slug': ('name',)}
	autocomplete_fields = ('category', 'genre')
	inlines = [ProductImageInline]


class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	search_fields = ('name',)
	prepopulated_fields = {'slug': ('name',)}


class GenreAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'position', 'slug')
	list_filter = ('category',)
	search_fields = ('name',)
	prepopulated_fields = {'slug': ('name',)}
 

admin.site.register(Category, CategoryAdmin)
admin.site.register(Genre, GenreAdmin)
admin.site.register(Product, ProductAdmin)
