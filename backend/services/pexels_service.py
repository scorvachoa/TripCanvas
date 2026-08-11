"""Servicio para buscar fotos del destino en Pexels (API gratuita).

Gemini (texto) propone una búsqueda por tarjeta (`image_query`) y aquí se
descarga una URL de foto real. La URL se guarda en `card.image`; al renderizar
(export_service) se incrusta en base64.
"""
import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
PEXELS_TIMEOUT_SECONDS = 20


def search_photo_urls(
    query: str, api_key: str, per_page: int = 5, orientation: str = "portrait"
) -> list[str]:
    """Busca fotos y devuelve sus URLs (`large2x`, ~1880px de lado mayor).

    Devuelve la lista en el orden de relevancia de Pexels; quien llama decide
    cuál usar (p. ej. para repartir variedad entre tarjetas). Vacía si no hay
    resultados o si la búsqueda falla.
    """
    if not query or not api_key:
        return []

    params = urllib.parse.urlencode(
        {"query": query, "per_page": per_page, "orientation": orientation}
    )
    req = urllib.request.Request(
        f"{PEXELS_SEARCH_URL}?{params}",
        headers={
            "Authorization": api_key,
            "User-Agent": "TripCanvas/1.0",
        },
    )

    with urllib.request.urlopen(req, timeout=PEXELS_TIMEOUT_SECONDS) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    photos = data.get("photos") or []
    urls: list[str] = []
    for photo in photos:
        src = photo.get("src") or {}
        url = src.get("large2x") or src.get("large") or src.get("original") or ""
        if url:
            urls.append(url)
    return urls
