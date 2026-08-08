"""Flujo completo real: Gemini -> API -> proyecto -> exportar."""
import io
import json
import struct
import zipfile

import requests

BASE = "http://127.0.0.1:8000"

# 1. Generar contenido real con Gemini
print("1. Generando con Gemini...")
r = requests.post(f"{BASE}/api/generate", json={
    "destination": "Machu Picchu",
    "category": "cinco_datos",
    "count": 2,
    "language": "es",
}, timeout=120)
assert r.status_code == 200, r.text
gen = r.json()
print(f"   OK — {len(gen['cards'])} tarjetas: {[c['title'][:40] for c in gen['cards']]}")

# 2. Guardar proyecto
print("2. Guardando proyecto...")
r = requests.post(f"{BASE}/api/projects", json={
    "name": "Flujo real completo",
    "destination": gen["destination"],
    "template": "cinco-datos",
    "format": "instagram_portrait",
    "cards": gen["cards"],
}, timeout=30)
assert r.status_code == 201, r.text
pid = r.json()["id"]
print(f"   OK — id={pid}")

# 3. Recuperar proyecto
print("3. Recuperando proyecto...")
r = requests.get(f"{BASE}/api/projects/{pid}")
assert r.status_code == 200, r.text
proj = r.json()
assert len(proj["cards"]) == 2
print(f"   OK — {proj['name']}, {len(proj['cards'])} tarjetas")

# 4. Exportar la primera tarjeta
print("4. Exportando PNG...")
r = requests.post(f"{BASE}/api/export", json={
    **proj["cards"][0],
    "destination": proj["destination"],
    "template_id": proj["template"],
    "format_id": proj["format"],
}, timeout=120)
assert r.status_code == 200, r.text
png = r.content
assert png[:8] == b"\x89PNG\r\n\x1a\n"
w, h = struct.unpack(">II", png[16:24])
assert (w, h) == (1080, 1350), (w, h)
print(f"   OK — {w}x{h}")

# 5. Exportar ZIP
print("5. Exportando ZIP...")
r = requests.post(f"{BASE}/api/export/all", json={
    "destination": proj["destination"],
    "category": "cinco_datos",
    "count": 2,
    "language": "es",
    "template_id": proj["template"],
    "format_id": proj["format"],
    "cards": proj["cards"],
}, timeout=180)
assert r.status_code == 200, r.text
zf = zipfile.ZipFile(io.BytesIO(r.content))
names = zf.namelist()
print(f"   OK — {names}")

# 6. Eliminar proyecto de prueba
requests.delete(f"{BASE}/api/projects/{pid}")

print("\nFLUJO COMPLETO OK")
