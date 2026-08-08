import json
import logging
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from config import GEMINI_API_KEYS, GEMINI_MODEL

logger = logging.getLogger(__name__)

CURL_TIMEOUT_SECONDS = 45

_RATE_LIMIT_HINTS = ("429", "quota", "rate limit", "resource exhausted")


class RateLimitError(ConnectionError):
    """La API devolvió un límite de cuota/tasa. Sirve para rotar de clave."""


class GeminiClient:
    """Cliente de Gemini con rotación automática de API keys.

    Usa `curl` vía subprocess: en entornos donde las conexiones directas de
    Python son lentas o están bloqueadas, curl es fiable y rápido. Ante un
    429 (quota/rate limit) rota a la siguiente clave configurada.
    """

    def __init__(self, api_keys: list[str] | None = None, model: str = GEMINI_MODEL):
        keys = [k for k in (api_keys or GEMINI_API_KEYS) if k]
        if not keys or any(k == "your_gemini_api_key_here" for k in keys):
            raise ValueError(
                "GEMINI_API_KEY no está configurada. Cópiala en el archivo .env"
            )
        if shutil.which("curl") is None:
            raise ValueError("No se encontró `curl` en el sistema.")
        self._keys = keys
        self._key_index = 0
        self._model_name = model

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

        with tempfile.TemporaryDirectory() as tmpdir:
            payload_path = Path(tmpdir) / "payload.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            payload_arg = str(payload_path).replace("\\", "/")

            # Config de curl: la API key va en el archivo de config, no en la CLI.
            config_path = Path(tmpdir) / "curl.conf"
            config_path.write_text(
                "\n".join(
                    [
                        f'url = "{self._endpoint()}"',
                        f'header = "x-goog-api-key: {api_key}"',
                        'header = "Content-Type: application/json"',
                        f'data = "@{payload_arg}"',
                        "--silent",
                        "--show-error",
                        f"--max-time {CURL_TIMEOUT_SECONDS}",
                        "--fail-with-body",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                ["curl", "-K", str(config_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=CURL_TIMEOUT_SECONDS + 15,
            )

        if result.returncode != 0:
            detail = ""
            if result.stdout:
                try:
                    body = json.loads(result.stdout)
                    detail = body.get("error", {}).get("message", "")
                except (json.JSONDecodeError, AttributeError):
                    detail = result.stdout.strip()[:300]
            combined = f"{result.returncode} {result.stderr} {detail}".lower()
            if any(hint in combined for hint in _RATE_LIMIT_HINTS):
                raise RateLimitError(f"Quota/rate limit: {detail}".strip())
            raise ConnectionError(
                f"Fallo de red al consultar Gemini ({result.returncode}). {detail}".strip()
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            logger.error("Respuesta no JSON de Gemini: %s", result.stdout[:500])
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


@lru_cache(maxsize=1)
def get_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client


def reset_client() -> None:
    global _client
    _client = None
    get_client.cache_clear()
