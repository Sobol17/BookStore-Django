import logging
import uuid
from typing import Optional, Tuple

from django.conf import settings

logger = logging.getLogger(__name__)


class YoukassaConfigurationError(RuntimeError):
    """Raised when YooKassa settings are missing."""


class YoukassaAPIError(RuntimeError):
    """Raised when YooKassa API call fails."""


def _configure():
    """Configure YooKassa SDK with credentials from settings."""
    from yookassa import Configuration

    shop_id = getattr(settings, 'YOUKASSA_SHOP_ID', '')
    secret_key = getattr(settings, 'YOUKASSA_SECRET_KEY', '')

    if not shop_id or not secret_key:
        raise YoukassaConfigurationError(
            'YOUKASSA_SHOP_ID and YOUKASSA_SECRET_KEY must be configured.'
        )

    Configuration.account_id = shop_id
    Configuration.secret_key = secret_key


def create_sbp_payment(order, return_url: str) -> Tuple[str, str]:
    """
    Create an SBP payment in YooKassa.

    Returns (payment_id, confirmation_url).
    Raises YoukassaConfigurationError or YoukassaAPIError on failure.
    """
    from yookassa import Payment
    from yookassa.domain.exceptions import ApiError

    _configure()

    idempotency_key = str(uuid.uuid4())

    payment_request = {
        'amount': {
            'value': f'{order.total_price:.2f}',
            'currency': 'RUB',
        },
        'confirmation': {
            'type': 'redirect',
            'return_url': return_url,
        },
        'capture': True,
        'description': f'Заказ №{order.id}',
        'payment_method_data': {
            'type': 'sbp',
        },
        'metadata': {
            'order_id': str(order.id),
        },
    }

    try:
        payment = Payment.create(payment_request, idempotency_key)
    except ApiError as exc:
        logger.error('YooKassa API error for order %s: %s', order.id, exc)
        raise YoukassaAPIError(f'YooKassa API error: {exc}') from exc
    except Exception as exc:
        logger.exception('Unexpected error creating YooKassa payment for order %s', order.id)
        raise YoukassaAPIError('Failed to create YooKassa payment.') from exc

    confirmation_url = payment.confirmation.confirmation_url
    logger.info(
        'YooKassa payment created for order %s: payment_id=%s',
        order.id,
        payment.id,
    )
    return payment.id, confirmation_url


def fetch_payment(payment_id: str) -> Optional[object]:
    """Fetch a payment from YooKassa by ID to verify its status."""
    from yookassa import Payment
    from yookassa.domain.exceptions import ApiError

    _configure()

    try:
        return Payment.find_one(payment_id)
    except ApiError as exc:
        logger.error('YooKassa fetch payment error for %s: %s', payment_id, exc)
        return None
    except Exception:
        logger.exception('Unexpected error fetching YooKassa payment %s', payment_id)
        return None
