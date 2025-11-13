from django.db.models import Count, Q, Avg
from django.db.models.functions import Coalesce
from .models import Category, Product


def get_categories_with_products():
    return Category.objects.annotate(
        products_count=Count(
            'products',
            filter=Q(products__is_published=True),
        )
    ).filter(products_count__gt=0)


def with_review_stats(queryset):
    return queryset.annotate(
        reviews_total=Count(
            'reviews',
            filter=Q(reviews__is_public=True),
        ),
        reviews_average=Coalesce(
            Avg(
                'reviews__rating',
                filter=Q(reviews__is_public=True),
            ),
            0.0,
        ),
    )


def get_published_products_queryset():
    queryset = Product.objects.filter(is_published=True)
    return with_review_stats(queryset).order_by('-created_at')


def get_related_products(product, limit=8):
    queryset = (
        Product.objects.filter(
            category=product.category,
            is_published=True,
        )
        .exclude(id=product.id)
        .order_by('-created_at')
    )
    return with_review_stats(queryset)[:limit]
    

def get_products_collection(collection, limit=8):
    queryset = Product.objects.filter(
        collection=collection,
        is_published=True
    ).order_by('-created_at')
    return with_review_stats(queryset)[:limit]
    
