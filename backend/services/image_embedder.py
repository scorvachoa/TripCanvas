"""Descarga, validación y embedding de imágenes en HTML.

Gestiona la allowlist de dominios (anti-SSRF), la descarga de imágenes
y su conversión a data URLs base64 para incrustar en el HTML de exportación.
"""

import base64
import html as html_module
import logging
import mimetypes
import re
import urllib.request
from functools import lru_cache
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_ALLOWED_IMAGE_HOSTS = frozenset({
    "images.pexels.com",
    "images.unsplash.com",
})


def is_allowed_image_host(url: str) -> bool:
    """Verifica que la URL pertenezca a un dominio de imágenes permitido."""
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return any(host == h or host.endswith("." + h) for h in _ALLOWED_IMAGE_HOSTS)


@lru_cache(maxsize=64)
def _fetch_embed(url: str) -> str:
    """Descarga la imagen y la devuelve como data URL base64 (cacheado).

    La caché evita volver a descargar la misma imagen en cada render del
    preview/export. Si no se puede descargar, devuelve la URL original.
    Solo descarga de dominios en la allowlist para prevenir SSRF.
    """
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) "
                "Gecko/20100101 Firefox/130.0"
            ),
            "Accept": "image/avif,image/webp,image/png,image/*;q=0.8,*/*;q=0.5",
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type", "")
        if len(data) > 8 * 1024 * 1024:
            logger.warning("Imagen demasiado grande para incrustar (%d bytes); usando URL", len(data))
            return url
        if not ctype or ctype.startswith("text/"):
            ctype = mimetypes.guess_type(url)[0] or "image/png"
        return f"data:{ctype};base64,{base64.b64encode(data).decode('ascii')}"
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo incrustar la imagen (%s); usando URL", exc)
        return url


def embed_image(value) -> str:
    """Devuelve la imagen como data URL base64 si es posible.

    Al incrustar la imagen en el HTML de exportación el PNG ya no depende de que
    el servidor (Playwright) pueda alcanzar la URL original (403 externos,
    hotlink, firewalls, etc.) que sí carga el navegador del usuario en la
    preview. Si no se puede descargar, devuelve la URL original.

    Solo procesa URLs de dominios permitidos (allowlist) para prevenir SSRF.
    """
    url = str(value or "").strip()
    if not url or url.startswith("data:"):
        return url
    if not url.lower().startswith(("http://", "https://")):
        logger.warning("URL de imagen con esquema no permitido; se omite el incrustado")
        return url
    if not is_allowed_image_host(url):
        logger.warning("URL de imagen con dominio no permitido; se omite el incrustado")
        return url
    return _fetch_embed(url)


def escape_image_url(value) -> str:
    """Sanitiza una URL de imagen para usarla dentro de url('...').

    Reemplaza comillas y backslashes para que no rompa el atributo style ni la
    cadena CSS, y escapa el resto de caracteres especiales de HTML.
    """
    url = str(value or "").strip()
    url = url.replace("'", "%27").replace('"', "%22").replace("\\", "/")
    return html_module.escape(url, quote=False)


def inject_card_photo(card_html: str, image: str) -> str:
    """Añade la foto como fondo de .travel-card para cualquier plantilla."""
    bg_style = (
        "background-image:linear-gradient(var(--tc-overlay),var(--tc-overlay)),"
        f"url('{escape_image_url(image)}');"
        "background-size:cover;background-position:center;"
    )
    return re.sub(
        r'<div class="travel-card([^"]*)"([^>]*)>',
        lambda m: f'<div class="travel-card{m.group(1)} tc-has-photo"{m.group(2)} style="{bg_style}">',
        card_html,
        count=1,
    )


def inject_format_class(card_html: str, cls: str) -> str:
    """Añade una clase modificadora (ej. tc-square) al .travel-card."""
    return re.sub(
        r'<div class="travel-card([^"]*)"([^>]*)>',
        lambda m: f'<div class="travel-card{m.group(1)} {cls}"{m.group(2)}>',
        card_html,
        count=1,
    )
