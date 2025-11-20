import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request

from django.core.exceptions import AppRegistryNotReady
from django.db import DatabaseError

from .models import DeepSeekPrompt


logger = logging.getLogger(__name__)

DETAILS_PLACEHOLDER = '{details}'
DETAILS_HEADER = 'Используй следующие сведения:'
DEFAULT_PROMPT_TEMPLATE = (
    'Ты — литературный критик. Сформулируй по-русски выразительную рецензию из 2–3 абзацев, '
    'делай акцент на идеях и стиле произведения. Не пересказывай сюжет подробно и уложись примерно в 1200 символов.\n'
    f'{DETAILS_PLACEHOLDER}'
)


class DeepSeekConfigurationError(RuntimeError):
    """Raised when DeepSeek API settings are missing."""


class DeepSeekAPIError(RuntimeError):
    """Raised when DeepSeek API responds with an error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


@dataclass
class DeepSeekReviewService:
    api_key: str
    api_url: str
    model: str
    timeout: int = 30
    temperature: float = 0.6
    max_tokens: int = 800

    def __post_init__(self) -> None:
        if not self.api_key:
            raise DeepSeekConfigurationError('DeepSeek API key is not configured.')
        if not self.api_url:
            raise DeepSeekConfigurationError('DeepSeek API URL is not configured.')
        if not self.model:
            raise DeepSeekConfigurationError('DeepSeek model name was not provided.')

    def generate_review(
        self,
        *,
        title: str,
        authors: Optional[str] = None,
        year: Optional[int] = None,
        genre: Optional[str] = None,
    ) -> str:
        """
        Builds prompt and requests literary review text from DeepSeek API.
        """
        prompt = self._build_prompt(title=title, authors=authors, year=year, genre=genre)
        payload = self._build_payload(prompt)
        response_data = self._perform_request(payload)
        return self._extract_content(response_data)

    def _build_prompt(
        self,
        *,
        title: str,
        authors: Optional[str],
        year: Optional[int],
        genre: Optional[str],
    ) -> str:
        details = [f'Название: «{title.strip()}»']
        if authors:
            details.append(f'Автор: {authors.strip()}')
        if year:
            details.append(f'Год: {year}')
        if genre:
            details.append(f'Жанр: {genre}')
        details_text = '\n'.join(f'- {item}' for item in details)
        details_block = f'{DETAILS_HEADER}\n{details_text}'
        template = self._get_prompt_template()
        if DETAILS_PLACEHOLDER in template:
            return template.replace(DETAILS_PLACEHOLDER, details_block)
        template = template.rstrip()
        separator = '\n' if template else ''
        return f'{template}{separator}{details_block}'

    def _build_payload(self, prompt: str) -> Dict[str, Any]:
        return {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        'Ты опытный литературный обозреватель. Пиши живым языком, не скатывайся в рекламные клише '
                        'и отвечай только на русском.'
                    ),
                },
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
        }

    def _perform_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload).encode('utf-8')
        req = request.Request(self.api_url, data=data, method='POST')
        req.add_header('Authorization', f'Bearer {self.api_key}')
        req.add_header('Content-Type', 'application/json')
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset() or 'utf-8'
                body = response.read().decode(charset)
        except error.HTTPError as exc:
            detail = self._read_error_body(exc)
            logger.warning('DeepSeek API responded with %s: %s', exc.code, detail or 'no body')
            raise DeepSeekAPIError(
                'DeepSeek API вернул ошибку.',
                status_code=exc.code,
                response_body=detail,
            ) from exc
        except error.URLError as exc:
            logger.error('DeepSeek API connection error: %s', exc.reason)
            raise DeepSeekAPIError('Не удалось связаться с DeepSeek API.') from exc
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            logger.error('DeepSeek API returned invalid JSON: %s', exc)
            raise DeepSeekAPIError('Не удалось обработать ответ DeepSeek API.') from exc

    def _extract_content(self, payload: Dict[str, Any]) -> str:
        choices = payload.get('choices') or []
        if not choices:
            raise DeepSeekAPIError('Ответ DeepSeek не содержит текста рецензии.')
        message = choices[0].get('message') or {}
        content = (message.get('content') or '').strip()
        if not content:
            raise DeepSeekAPIError('DeepSeek не вернул текст рецензии.')
        return content

    def _get_prompt_template(self) -> str:
        saved_prompt = self._load_prompt_from_db()
        return saved_prompt or DEFAULT_PROMPT_TEMPLATE

    @staticmethod
    def _load_prompt_from_db() -> Optional[str]:
        try:
            prompt_text = (
                DeepSeekPrompt.objects.order_by('-updated_at').values_list('text', flat=True).first()
            )
        except (DatabaseError, AppRegistryNotReady) as exc:
            logger.warning('DeepSeek prompt is not available yet: %s', exc)
            return None
        except Exception:
            logger.exception('Failed to load DeepSeek prompt from the database.')
            return None
        if prompt_text:
            return prompt_text.strip()
        return None

    @staticmethod
    def _read_error_body(exc: error.HTTPError) -> Optional[str]:
        try:
            data = exc.read()
        except Exception:
            return None
        try:
            return data.decode('utf-8')
        except Exception:
            return None
