from typing import Optional

from django.db import transaction

from .models import FavoriteItem, FavoriteList


def _ensure_session_key(request) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _release_conflicting_session_keys(session_key: str) -> None:
    FavoriteList.objects.filter(session_key=session_key).exclude(user=None).update(session_key=None)


def _get_existing_session_list(session_key: str) -> Optional[FavoriteList]:
    _release_conflicting_session_keys(session_key)
    return FavoriteList.objects.filter(session_key=session_key, user=None).first()


def _get_or_create_session_list(session_key: str) -> FavoriteList:
    _release_conflicting_session_keys(session_key)
    favorite_list, _ = FavoriteList.objects.get_or_create(session_key=session_key, user=None)
    return favorite_list


def merge_session_favorites(request, user) -> FavoriteList:
    session_key = _ensure_session_key(request)
    session_list = _get_existing_session_list(session_key)
    user_list, _ = FavoriteList.objects.get_or_create(user=user)

    if session_list and session_list != user_list:
        with transaction.atomic():
            for item in session_list.items.select_related('product'):
                FavoriteItem.objects.get_or_create(
                    favorite_list=user_list,
                    product=item.product,
                )
        session_list.delete()

    request.favorite_list = user_list
    return user_list


def resolve_favorite_list(request) -> FavoriteList:
    session_key = _ensure_session_key(request)

    if request.user.is_authenticated:
        return merge_session_favorites(request, request.user)

    favorite_list = _get_or_create_session_list(session_key)
    request.favorite_list = favorite_list
    return favorite_list
