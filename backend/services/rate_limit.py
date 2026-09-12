"""Rate limiting simple en memoria para endpoints sensibles.

Evita abuso de coste (p. ej. llamadas ilimitadas a Gemini). Estado en memoria:
se reinicia al reiniciar el servidor, suficiente para un backend local.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW_SECONDS = 60

_hits: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(request: Request, max_requests: int = RATE_LIMIT_MAX, window_seconds: int = RATE_LIMIT_WINDOW_SECONDS) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = _hits[client]
    while window and now - window[0] > window_seconds:
        window.pop(0)
    if len(window) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes. Inténtalo en unos segundos.",
        )
    window.append(now)


def rate_limit(
    max_requests: int = RATE_LIMIT_MAX,
    window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
):
    def dependency(request: Request) -> None:
        _check_rate_limit(request, max_requests, window_seconds)

    return dependency
