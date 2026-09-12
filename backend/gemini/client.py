"""Cliente HTTP para la API de Google Gemini.

Usa httpx para realizar las peticiones. Incluye rotación automática de API
keys ante errores 429 (quota/rate limit).
"""

import json
import logging

import httpx

from config import GEMINI_API_KEYS, GEMINI_MODEL

logger = logging.getLogger(__name__)

HTTP_TIMEOUT_SECONDS = 45

_RATE_LIMIT_HINTS = ("429", "quota", "rate limit", "resource exhausted")


class RateLimitError(ConnectionError):
    """La API devolvió un límite de cuota/tasa. Sirve para rotar de clave."""


class GeminiClient:
    """Cliente de Gemini con rotación automática de API keys.

    Usa httpx para las peticiones HTTP. Ante un 429 (quota/rate limit) rota
    a la siguiente clave configurada.
    """

    def __init__(self, api_keys: list[str] | None = None, model: str = GEMINI_MODEL):
        keys = [k for k in (api_keys or GEMINI_API_KEYS) if k]
        if not keys or any(k == "your_gemini_api_key_here" for k in keys):
            raise ValueError(
                "GEMINI_API_KEY no está configurada. Cópiala en el archivo .env"
            )
        self._keys = keys
        self._key_index = 0
        self._model_name = model
        self._client = httpx.Client(timeout=HTTP_TIMEOUT_SECONDS)

    def _current_key(self) -> str:
        return self._keys[self._key_index % len(self._keys)]

    def _rotate(self) -> None:
        self._key_index = (self._key_index + 1) % len(self._keys)

    def _endpoint(self) -> str:
        return (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{self._model_name}:generateContent"
        )

    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Genera contenido. Reintenta con la siguiente clave ante 429/quota."""
        attempts = len(self._keys)
        last_err: Exception | None = None
        for _ in range(attempts):
            key = self._current_key()
            try:
                return self._generate_once(prompt, temperature, key)
            except RateLimitError as exc:
                logger.warning(
                    "Quota/rate limit con una clave; rotando a la siguiente (%d claves). %s",
                    len(self._keys),
                    exc,
                )
                last_err = exc
                self._rotate()
            except ConnectionError as exc:
                last_err = exc
                self._rotate()
                if self._key_index == 0:
                    break
        if isinstance(last_err, RateLimitError):
            raise RateLimitError(
                "Todas las claves configuradas superaron su cuota/límite. "
                "Espera unos segundos o añade más claves en GEMINI_API_KEYS."
            )
        raise last_err or ConnectionError("Fallo de red al consultar Gemini.")

    def _generate_once(self, prompt: str, temperature: float, api_key: str) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }

        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }

        try:
            response = self._client.post(self._endpoint(), json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise ConnectionError(f"Timeout al consultar Gemini: {exc}") from exc
        except httpx.RequestError as exc:
            raise ConnectionError(f"Fallo de red al consultar Gemini: {exc}") from exc

        if response.status_code != 200:
            detail = ""
            try:
                body = response.json()
                detail = body.get("error", {}).get("message", "")
            except (json.JSONDecodeError, AttributeError):
                detail = response.text.strip()[:300]
            combined = f"{response.status_code} {detail}".lower()
            if any(hint in combined for hint in _RATE_LIMIT_HINTS):
                raise RateLimitError(f"Quota/rate limit: {detail}".strip())
            raise ConnectionError(
                f"Fallo de red al consultar Gemini ({response.status_code}). {detail}".strip()
            )

        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error("Respuesta no JSON de Gemini: %s", response.text[:500])
            raise ValueError("Gemini devolvió una respuesta inválida.")

        if "error" in data:
            err = data["error"]
            message = err.get("message", str(err))
            if any(hint in str(err).lower() or hint in message.lower() for hint in _RATE_LIMIT_HINTS):
                raise RateLimitError(f"Quota/rate limit: {message}")
            raise ConnectionError(f"Gemini error: {message}")

        candidates = data.get("candidates") or []
        if not candidates:
            raise ValueError("Gemini no devolvió contenido.")
        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return text or ""


_client: GeminiClient | None = None


def get_client() -> GeminiClient:
    """Devuelve la instancia singleton del cliente Gemini."""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


def reset_client() -> None:
    """Reinicia la instancia del cliente (útil para tests)."""
    global _client
    if _client is not None:
        _client._client.close()
    _client = None
