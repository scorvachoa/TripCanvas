import html as html_module
import io
import json
import logging
import re
import zipfile
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
                f"<div class='fv-row'><span class='fv-label'>{_esc(label)}</span>"
                f"<span class='fv-value'>{_esc(value)}</span></div>"
            )
        else:
            rows.append(f"<div class='fv-row'><span class='fv-value'>{_esc(fact)}</span></div>")
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
    facts_type = "label_value" if isinstance(card.facts[:1], dict) or (card.facts and isinstance(card.facts[0], dict)) else "list"
    facts_html = (
        _render_facts_label_value(card.facts)
        if facts_type == "label_value"
        else _render_facts_list(card.facts)
    )

    logo = LOGO_HTML if design.get("showLogo", True) else ""

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
        "IMAGE": _esc(card.image or ""),
        "IMAGE_QUERY": _esc(card.image_query),
        "LOGO": logo,
        "BG": _esc(design.get("background", DEFAULT_DESIGN["background"])),
        "TEXT": _esc(design.get("text", DEFAULT_DESIGN["text"])),
        "ACCENT": _esc(design.get("accent", DEFAULT_DESIGN["accent"])),
        "OVERLAY": _esc(design.get("overlay", DEFAULT_DESIGN["overlay"])),
        "FONT": _esc(design.get("font", DEFAULT_DESIGN["font"])),
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

    css_vars = (
        "--tc-bg: var(--bg); --tc-text: var(--text); --tc-accent: var(--accent); "
        f"--tc-overlay: var(--overlay); --tc-text-scale: {design.get('textScale', 1)};"
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
}}

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
) -> Path:
    """Genera un PNG de la tarjeta usando Playwright con el HTML renderizado."""
    html_content = render_card_html(
        card, template_id, destination=destination, format_id=format_id, design=design
    )
    return await _capture_png(html_content, format_id, suffix=card.number or 1)


async def _capture_png(html_content: str, format_id: str, suffix=1) -> Path:
    from playwright.async_api import async_playwright

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    width, height = format_size(format_id)

    file_path = OUTPUT_DIR / f"card_{suffix:02d}.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.set_content(html_content, wait_until="networkidle")
        element = page.locator(".travel-card")
        await element.screenshot(path=str(file_path))
        await browser.close()

    return file_path


async def export_cards_zip(
    cards: list[Card],
    template_id: str,
    destination: str = "",
    format_id: str = "instagram_portrait",
    design: dict | None = None,
) -> Path:
    """Genera un ZIP con las tarjetas en PNG y un copy.txt con los textos."""
    from playwright.async_api import async_playwright

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    width, height = format_size(format_id)
    safe_dest = re.sub(r"[^a-z0-9_]+", "_", destination.lower()).strip("_") or "tripcanvas"
    zip_path = OUTPUT_DIR / f"tripcanvas_{safe_dest}.zip"

    pages: list[tuple[Path, Card]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for i, card in enumerate(cards, start=1):
            html_content = render_card_html(
                card,
                template_id,
                destination=destination,
                format_id=format_id,
                design=design,
            )
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.set_content(html_content, wait_until="networkidle")
            element = page.locator(".travel-card")
            png_path = OUTPUT_DIR / f"_bulk_{i:02d}.png"
            await element.screenshot(path=str(png_path))
            pages.append((png_path, card))
            await page.close()
        await browser.close()

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
