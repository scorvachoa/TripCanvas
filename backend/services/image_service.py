import logging
import urllib.parse

logger = logging.getLogger(__name__)


def get_placeholder_image_url(query: str = "Peru travel", width: int = 800) -> str:
    """Devuelve una URL de imagen de Unsplash Source como proveedor inicial.

    No bloquea el sistema: si no hay servicio configurado se usa un placeholder
    local (gradiente) en el frontend.
    """
    encoded = urllib.parse.quote(query)
    return f"https://source.unsplash.com/{width}x1000/?{encoded}"


def image_url_for(card_image: str | None, image_query: str = "") -> str | None:
    if card_image:
        return card_image
    query = image_query or "Peru travel"
    return get_placeholder_image_url(query)
