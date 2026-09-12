"""Gestión del navegador Chromium (Playwright) para exportación PNG.

Mantiene una instancia compartida del navegador para reutilizar entre
peticiones y encapsula la captura de screenshots.
"""

import logging
from pathlib import Path

from config import OUTPUT_DIR
from services.template_service import format_size

logger = logging.getLogger(__name__)

_playwright = None
_browser = None
_browser_lock = None


async def get_browser():
    """Devuelve un navegador Chromium compartido, lanzándolo si es necesario.

    Lanzar Chromium cuesta ~1-2s; al reutilizar la instancia entre peticiones
    las exportaciones sucesivas son mucho más rápidas. ``asyncio.Lock`` evita que
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
        # --no-sandbox es necesario al correr como root (Docker/Render);
        # no afecta al desarrollo local.
        _browser = await _playwright.chromium.launch(args=["--no-sandbox"])
        return _browser


async def close_browser() -> None:
    """Cierra el navegador y el runtime de Playwright (llamar al apagar la app)."""
    global _playwright, _browser
    if _browser is not None:
        try:
            await _browser.close()
        except Exception:  # noqa: BLE001
            logger.warning("Error al cerrar el navegador Chromium", exc_info=True)
        _browser = None
    if _playwright is not None:
        try:
            await _playwright.stop()
        except Exception:  # noqa: BLE001
            logger.warning("Error al detener Playwright", exc_info=True)
        _playwright = None


async def capture_png(
    html_content: str,
    format_id: str,
    suffix: int = 1,
    output_dir: Path | None = None,
) -> Path:
    """Captura un screenshot del HTML renderizado como PNG."""
    out = output_dir or OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    width, height = format_size(format_id)

    file_path = out / f"card_{suffix:02d}.png"

    browser = await get_browser()
    page = await browser.new_page(viewport={"width": width, "height": height})
    try:
        await page.set_content(html_content, wait_until="networkidle")
        element = page.locator(".travel-card")
        await element.screenshot(path=str(file_path))
    finally:
        await page.close()

    return file_path
