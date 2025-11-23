import re


class PhoneValidationError(ValueError):
    """Raised when a phone number can't be normalized."""


def normalize_phone(value: str) -> str:
    """Convert different Russian phone formats to +7XXXXXXXXXX."""

    digits = re.sub(r'\D', '', value or '')
    if not digits:
        raise PhoneValidationError('Введите номер телефона')

    if digits[0] in {'7', '8'}:
        digits = digits[1:]

    if len(digits) > 10:
        digits = digits[-10:]

    if len(digits) < 10:
        raise PhoneValidationError('Введите номер телефона полностью')

    return f'+7{digits}'
