from django.db.models import Count, Q
from .models import Category, Product


def get_categories_with_products():
    return Category.objects.annotate(
        products_count=Count(
            'products',
            filter=Q(products__is_published=True),
        )
    ).filter(products_count__gt=0)


def get_published_products_queryset():
    return Product.objects.filter(is_published=True).order_by('-created_at')


def get_related_products(product, limit=4):
    return Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:limit]
    

def get_products_collection(collection, limit=8):
    return Product.objects.filter(
        collection=collection,
        is_published=True
    ).order_by('-created_at')[:limit]
    
