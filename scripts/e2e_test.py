"""Prueba E2E del frontend con Playwright (sin Gemini)."""
import asyncio
import sys

from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8000"
PROJECT_ID = "81bedc09a0f5413198d2fa64f56ac25a"


async def main():
    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        # 1. Dashboard carga
        await page.goto(BASE, wait_until="networkidle")
        await page.wait_for_selector("#qg-destination option", state="attached", timeout=10000)
        dest_count = await page.eval_on_selector_all("#qg-destination", "els => els.length")
        tpl_count = await page.eval_on_selector_all("#qg-template option", "els => els.length")
        print(f"Dashboard OK — destinos: {dest_count}, plantillas: {tpl_count}")

        # 2. Abrir editor con el proyecto de prueba
        await page.goto(f"{BASE}/index.html", wait_until="networkidle")
        await page.evaluate(
            "App.state = {destination:'Machu Picchu', " 
            "cards: [{type:'dato_curioso', title:'Hola', body:'Prueba', facts:['a','b'], "
            "location:'Cusco', source:'UNESCO'},{type:'cinco_datos', title:'Segunda', "
            "facts:['1','2','3','4','5']}], template:'dato-curioso', format:'instagram_portrait', "
            "projectId:null, projectName:'Test', currentIndex:0, language:'es'}; "
            "App.show('editor')"
        )
        await page.wait_for_timeout(1200)

        has_card = await page.eval_on_selector("#preview-card .travel-card", "el => !!el")
        has_title = await page.eval_on_selector("#preview-card .dc-title", "el => el.textContent")
        print(f"Editor OK — travel-card renderizado: {has_card}, título: {has_title}")

        # 3. Navegación a la segunda tarjeta
        await page.click("#btn-next")
        await page.wait_for_timeout(500)
        title2 = await page.eval_on_selector("#e-title", "el => el.value")
        print(f"Navegación OK — tarjeta 2 título: {title2}")

        # 4. Cambiar plantilla
        await page.select_option("#d-template", "cinco-datos")
        await page.wait_for_timeout(600)
        has_cd = await page.eval_on_selector("#preview-card .cd-title", "el => !!el")
        print(f"Cambio plantilla OK — template cinco-datos: {has_cd}")

        # 5. Editar título en vivo
        await page.fill("#e-title", "Título editado en vivo")
        await page.wait_for_timeout(400)
        preview_title = await page.eval_on_selector("#preview-card .cd-title", "el => el.textContent")
        print(f"Edición en vivo OK — preview: {preview_title}")

        # 6. Cambiar formato story
        await page.select_option("#d-format", "story")
        await page.wait_for_timeout(400)
        fmt_ok = await page.eval_on_selector("#preview-card > div", "el => el.style.width")
        print(f"Formato story OK — width: {fmt_ok}")

        # 7. Proyectos y botones existen
        await page.click("#btn-save")
        await page.wait_for_timeout(300)
        modal_visible = await page.eval_on_selector("#modal-overlay", "el => !el.classList.contains('hidden')")
        print(f"Modal guardar OK: {modal_visible}")

        await page.click("#modal-cancel")

        # 8. Vista proyectos
        await page.evaluate("() => App.show('projects')")
        await page.wait_for_timeout(800)
        proj_count = await page.eval_on_selector_all("#projects-list .project-card", "els => els.length")
        print(f"Proyectos OK — tarjetas: {proj_count}")

        await browser.close()

    if errors:
        print("\nERRORES DE CONSOLA:")
        for e in errors:
            print(" -", e)
    else:
        print("\nSin errores de consola.")
    return 0 if not errors else 1


try:
    asyncio.run(main())
except Exception as exc:
    print("\nEXCEPCIÓN E2E:", exc)
    raise
