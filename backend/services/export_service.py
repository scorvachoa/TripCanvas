import html as html_module
import logging
import re
import urllib.request
import zipfile
from functools import lru_cache
from pathlib import Path

from config import OUTPUT_DIR
from models.content import Card
from services.template_service import format_size, load_template

logger = logging.getLogger(__name__)

DEFAULT_DESIGN = {
    "background": "#0f1a2e",
    "text": "#ffffff",
    "accent": "#f4b942",
    "overlay": "rgba(0,0,0,0.35)",
    "font": "'Poppins', 'Segoe UI', sans-serif",
    "showLogo": True,
    "textScale": 1,
}

LOGO_HTML = """
<div class="tc-logo"><span class="tc-logo-mark">&#9992;</span><span class="tc-logo-text">TRIPCANVAS</span></div>
"""

LOGO_CSS = """
.tc-logo {
  position: absolute;
  top: 34px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(0, 0, 0, 0.4);
  color: #ffffff;
  font-weight: 700;
  font-size: calc(var(--tc-text-scale) * 26px);
  letter-spacing: 0.08em;
  padding: 10px 22px;
  border-radius: 999px;
  z-index: 20;
  font-family: 'Inter', 'Segoe UI', sans-serif;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}
.tc-logo-mark { font-size: calc(var(--tc-text-scale) * 28px); line-height: 1; }
"""


def _esc(value) -> str:
    return html_module.escape(str(value or ""))


_CSS_VALUE_RE = re.compile(r"^[a-zA-Z0-9 #,.()%'\"\x27\x22\-\u00a0]+$")


def _css(value) -> str:
    """Sanitiza un valor destinado a CSS (colores, fuentes, overlay).

    No usa html.escape (rompe las comillas simples de los font-stack).
    Restringe a caracteres válidos de un valor CSS simple.
    """
    raw = str(value or "").strip()
    if not _CSS_VALUE_RE.match(raw):
        return ""
    return raw


def _image_url(value) -> str:
    """Sanitiza una URL de imagen para usarla dentro de url('...').

    Reemplaza comillas y backslashes para que no rompa el atributo style ni la
    cadena CSS, y escapa el resto de caracteres especiales de HTML.
    """
    url = str(value or "").strip()
    url = url.replace("'", "%27").replace('"', "%22").replace("\\", "/")
    return html_module.escape(url, quote=False)


@lru_cache(maxsize=64)
def _fetch_embed(url: str) -> str:
    """Descarga la imagen y la devuelve como data URL base64 (cacheado).

    La caché evita volver a descargar la misma imagen en cada render del
    preview/export. Si no se puede descargar, devuelve la URL original.
    """
    try:
        import base64
        import mimetypes

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


def _embed_image(value) -> str:
    """Devuelve la imagen como data URL base64 si es posible.

    Al incrustar la imagen en el HTML de exportación el PNG ya no depende de que
    el servidor (Playwright) pueda alcanzar la URL original (403 externos,
    hotlink, firewalls, etc.) que sí carga el navegador del usuario en la
    preview. Si no se puede descargar, devuelve la URL original.
    """
    url = str(value or "").strip()
    if not url or url.startswith("data:"):
        return url
    # Solo http/https: evitar SSRF/lectura de archivos locales vía file://, etc.
    if not url.lower().startswith(("http://", "https://")):
        logger.warning("URL de imagen con esquema no permitido; se omite el incrustado")
        return url
    return _fetch_embed(url)


def _inject_card_photo(card_html: str, image: str) -> str:
    """Añade la foto como fondo de .travel-card para cualquier plantilla."""
    bg_style = (
        "background-image:linear-gradient(var(--tc-overlay),var(--tc-overlay)),"
        f"url('{_image_url(image)}');"
        "background-size:cover;background-position:center;"
    )
    return re.sub(
        r'<div class="travel-card([^"]*)"([^>]*)>',
        lambda m: f'<div class="travel-card{m.group(1)} tc-has-photo"{m.group(2)} style="{bg_style}">',
        card_html,
        count=1,
    )


def _inject_format_class(card_html: str, cls: str) -> str:
    """Añade una clase modificadora (ej. tc-square) al .travel-card."""
    return re.sub(
        r'<div class="travel-card([^"]*)"([^>]*)>',
        lambda m: f'<div class="travel-card{m.group(1)} {cls}"{m.group(2)}>',
        card_html,
        count=1,
    )


def _render_facts_list(facts) -> str:
    items = []
    for i, fact in enumerate(facts or []):
        items.append(f"<li><span class='fact-num'>{i + 1}</span><span>{_esc(fact)}</span></li>")
    return "\n".join(items)


def _render_facts_label_value(facts) -> str:
    rows = []
    for fact in facts or []:
        if isinstance(fact, dict):
            label = fact.get("label", "")
            value = fact.get("value", "")
            rows.append(
                f"<li class='fv-row'><span class='fv-label'>{_esc(label)}</span>"
                f"<span class='fv-value'>{_esc(value)}</span></li>"
            )
        else:
            rows.append(
                f"<li class='fv-row'><span class='fv-value'>{_esc(fact)}</span></li>"
            )
    return "\n".join(rows)


def _render_options(options) -> str:
    letters = ["A", "B", "C", "D"]
    items = []
    for i, opt in enumerate(options or []):
        letter = letters[i] if i < len(letters) else str(i + 1)
        items.append(
            f"<div class='quiz-option'><span class='quiz-letter'>{letter}</span>"
            f"<span>{_esc(opt)}</span></div>"
        )
    return "\n".join(items)


def _render_items(items) -> str:
    rows = []
    for item in items or []:
        if isinstance(item, dict):
            label = item.get("label", "")
            value = item.get("value", "")
            rows.append(
                f"<div class='cmp-row'><span class='cmp-label'>{_esc(label)}</span>"
                f"<span class='cmp-value'>{_esc(value)}</span></div>"
            )
    return "\n".join(rows)


def _tokens(card: Card, destination: str, design: dict) -> dict[str, str]:
    extra = card.extra or {}
    facts_type = "label_value" if (card.facts and isinstance(card.facts[0], dict)) else "list"
    facts_html = (
        _render_facts_label_value(card.facts)
        if facts_type == "label_value"
        else _render_facts_list(card.facts)
    )

    logo = LOGO_HTML if design.get("showLogo", True) else ""

    image_url = card.image or ""
    image_style = (
        f"background-image:url('{_esc(image_url)}')" if image_url else ""
    )

    return {
        "DESTINATION": _esc(destination),
        "TITLE": _esc(card.title),
        "BODY": _esc(card.body),
        "QUESTION": _esc(card.question),
        "ANSWER": _esc(card.answer),
        "MYTH": _esc(card.myth),
        "REALITY": _esc(card.reality),
        "LOCATION": _esc(card.location),
        "ALTITUDE": _esc(card.altitude),
        "SOURCE": _esc(card.source),
        "NUMBER": _esc(card.number if card.number is not None else ""),
        "DATE": _esc(extra.get("fecha", "")),
        "FACTS_LIST": facts_html,
        "FACTS_LABEL_VALUE": facts_html,
        "OPTIONS": _render_options(card.options),
        "ITEMS": _render_items(extra.get("items", [])),
        "IMAGE": image_style,
        "IMAGE_QUERY": _esc(card.image_query),
        "LOGO": logo,
        "BG": _css(design.get("background", DEFAULT_DESIGN["background"])),
        "TEXT": _css(design.get("text", DEFAULT_DESIGN["text"])),
        "ACCENT": _css(design.get("accent", DEFAULT_DESIGN["accent"])),
        "OVERLAY": _css(design.get("overlay", DEFAULT_DESIGN["overlay"])),
        "FONT": _css(design.get("font", DEFAULT_DESIGN["font"])),
    }


def render_card_html(
    card: Card,
    template_id: str,
    destination: str = "",
    format_id: str = "instagram_portrait",
    design: dict | None = None,
) -> str:
    """Renderiza una tarjeta como página HTML completa lista para captura."""
    template = load_template(template_id)
    if template is None:
        raise ValueError(f"Plantilla no encontrada: {template_id}")

    design = {**DEFAULT_DESIGN, **(design or {})}
    width, height = format_size(format_id)
    tokens = _tokens(card, destination, design)

    card_html = template.html
    for key, value in tokens.items():
        card_html = card_html.replace("{{" + key + "}}", value)

    # Limpia cualquier token no reemplazado para evitar errores.
    card_html = re.sub(r"\{\{[A-Z_]+\}\}", "", card_html)

    # Foto como fondo de la tarjeta en cualquier plantilla. Se incrusta la
    # imagen en base64 para que el PNG sea fiel a lo que ve el usuario.
    image_src = _embed_image(card.image) if card.image else None
    if image_src:
        card_html = _inject_card_photo(card_html, image_src)

    # Formato corto (square): clase para compactar el diseño.
    if height <= 1100:
        card_html = _inject_format_class(card_html, "tc-square")

    text_scale = round(
        design.get("textScale", 1) * (0.82 if height <= 1100 else 1), 4
    )
    css_vars = (
        "--tc-bg: var(--bg); --tc-text: var(--text); --tc-accent: var(--accent); "
        f"--tc-overlay: var(--overlay); --tc-text-scale: {text_scale};"
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=Playfair+Display:wght@600;700;800&family=Inter:wght@400;600;700&display=swap');

:root {{
  --bg: {tokens['BG']};
  --text: {tokens['TEXT']};
  --accent: {tokens['ACCENT']};
  --overlay: {tokens['OVERLAY']};
  {css_vars}
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

.travel-card {{
  width: {width}px;
  height: {height}px;
  position: relative;
  overflow: hidden;
  font-family: {tokens['FONT']};
  container: tc / size;
}}

.travel-card.tc-has-photo {{ --tc-photo-shadow: 0 1px 2px rgba(0,0,0,0.55), 0 3px 10px rgba(0,0,0,0.3); }}
.travel-card.tc-has-photo :where(*) {{ text-shadow: var(--tc-photo-shadow); }}
.travel-card.tc-has-photo .dc-badge,
.travel-card.tc-has-photo .sq-badge,
.travel-card.tc-has-photo .hi-label,
.travel-card.tc-has-photo .qz-badge,
.travel-card.tc-has-photo .cp-badge,
.travel-card.tc-has-photo .gr-badge,
.travel-card.tc-has-photo .cj-badge,
.travel-card.tc-has-photo .cu-badge,
.travel-card.tc-has-photo .ar-spec,
.travel-card.tc-has-photo .na-badge,
.travel-card.tc-has-photo .ll-badge,
.travel-card.tc-has-photo .me-badge,
.travel-card.tc-has-photo .ig-badge,
.travel-card.tc-has-photo .cd-label,
.travel-card.tc-has-photo .mr-badge {{ text-shadow: none; }}

{LOGO_CSS}
{template.css}
</style>
</head>
<body>
{card_html}
</body>
</html>"""


async def export_card_png(
    card: Card,
    template_id: str,
    destination: str = "",
    format_id: str = "instagram_portrait",
    design: dict | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Genera un PNG de la tarjeta usando Playwright con el HTML renderizado."""
    html_content = render_card_html(
        card, template_id, destination=destination, format_id=format_id, design=design
    )
    return await _capture_png(html_content, format_id, suffix=card.number or 1, output_dir=output_dir)


async def _get_browser():
    """Devuelve un navegador Chromium compartido, lanzándolo si es necesario.

    Lanzar Chromium cuesta ~1-2s; al reutilizar la instancia entre peticiones
    las exportaciones sucesivas son mucho más rápidas. `asyncio.Lock` evita que
    dos peticiones concurrentes lancen dos navegadores.
    """
    global _playwright, _browser, _browser_lock
    if _browser_lock is None:
        import asyncio

        _browser_lock = asyncio.Lock()
    async with _browser_lock:
        if _browser is not None and _browser.is_connected():
            return _browser
        from playwright.async_api import async_playwright

        if _playwright is None:
            _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch()
        return _browser


async def _close_browser() -> None:
    """Cierra el navegador y el runtime de Playwright (llamar al apagar la app)."""
    global _playwright, _browser
    if _browser is not None:
        try:
            await _browser.close()
        except Exception:  # noqa: BLE001
            pass
        _browser = None
    if _playwright is not None:
        try:
            await _playwright.stop()
        except Exception:  # noqa: BLE001
            pass
        _playwright = None


_playwright = None
_browser = None
_browser_lock = None


async def _capture_png(html_content: str, format_id: str, suffix=1, output_dir: Path | None = None) -> Path:
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    width, height = format_size(format_id)

    file_path = out / f"card_{suffix:02d}.png"

    browser = await _get_browser()
    page = await browser.new_page(viewport={"width": width, "height": height})
    try:
        await page.set_content(html_content, wait_until="networkidle")
        element = page.locator(".travel-card")
        await element.screenshot(path=str(file_path))
    finally:
        await page.close()

    return file_path


async def export_cards_zip(
    cards: list[Card],
    template_id: str,
    destination: str = "",
    format_id: str = "instagram_portrait",
    design: dict | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Genera un ZIP con las tarjetas en PNG y un copy.txt con los textos."""
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    width, height = format_size(format_id)
    safe_dest = re.sub(r"[^a-z0-9_]+", "_", destination.lower()).strip("_") or "tripcanvas"
    zip_path = out / f"tripcanvas_{safe_dest}.zip"

    pages: list[tuple[Path, Card]] = []

    browser = await _get_browser()
    for i, card in enumerate(cards, start=1):
        html_content = render_card_html(
            card,
            template_id,
            destination=destination,
            format_id=format_id,
            design=design,
        )
        page = await browser.new_page(viewport={"width": width, "height": height})
        try:
            await page.set_content(html_content, wait_until="networkidle")
            element = page.locator(".travel-card")
            png_path = out / f"_bulk_{i:02d}.png"
            await element.screenshot(path=str(png_path))
            pages.append((png_path, card))
        finally:
            await page.close()

    with zipfile.ZipFile(zip_path, "w") as zf:
        for i, (png_path, card) in enumerate(pages, start=1):
            zf.write(png_path, f"{i:02d}_{card.type or 'card'}.png")
            png_path.unlink(missing_ok=True)

        copy_text = _build_copy_text(cards, destination)
        zf.writestr("copy.txt", copy_text)

    return zip_path


def _build_copy_text(cards: list[Card], destination: str) -> str:
    lines = [f"TRIPCANVAS — {destination.upper()}\n", "=" * 40, ""]
    for i, card in enumerate(cards, start=1):
        lines.append(f"TARJETA {i} — {card.type.replace('_', ' ').upper()}")
        lines.append(f"Título: {card.title}")
        if card.body:
            lines.append(f"Texto: {card.body}")
        if card.facts:
            lines.append("Datos:")
            for fact in card.facts:
                if isinstance(fact, dict):
                    lines.append(f"  • {fact.get('label', '')}: {fact.get('value', '')}")
                else:
                    lines.append(f"  • {fact}")
        if card.question:
            lines.append(f"Pregunta: {card.question}")
        if card.answer:
            lines.append(f"Respuesta: {card.answer}")
        if card.myth:
            lines.append(f"Mito: {card.myth}")
        if card.reality:
            lines.append(f"Realidad: {card.reality}")
        if card.location:
            lines.append(f"Ubicación: {card.location}")
        if card.altitude:
            lines.append(f"Altitud: {card.altitude}")
        if card.source:
            lines.append(f"Fuente: {card.source}")
        lines.append("")
        lines.append("-" * 40)
        lines.append("")
    return "\n".join(lines)
