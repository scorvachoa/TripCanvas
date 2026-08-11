"""Prueba de exportación: PNG individual y ZIP masivo."""
import io
import json
import sys
import zipfile

import requests

BASE = "http://127.0.0.1:8000"

cards = [
    {
        "type": "dato_curioso",
        "title": "Machu Picchu estuvo oculta durante siglos",
        "body": "La ciudadela permaneció desconocida para el mundo hasta su redescubrimiento.",
        "facts": [],
        "location": "Cusco, Perú",
        "altitude": "2430 m s. n. m.",
        "source": "UNESCO",
    },
    {
        "type": "cinco_datos",
        "title": "5 datos sobre Machu Picchu",
        "facts": ["Declarada Patrimonio de la Humanidad", "Siglo XV", "2430 m", "200+ estructuras", "Oculta por vegetación"],
        "location": "Cusco, Perú",
        "source": "UNESCO",
    },
    {
        "type": "mito_realidad",
        "title": "El fin del imperio inca",
        "myth": "Los españoles nunca encontraron Machu Picchu",
        "reality": "Fue olvidada por el mundo, no destruida",
        "location": "Cusco, Perú",
        "source": "UNESCO",
    },
]

# 1. Export individual
r = requests.post(f"{BASE}/api/export", json={
    **cards[0],
    "destination": "Machu Picchu",
    "template_id": "dato-curioso",
    "format_id": "instagram_portrait",
})
assert r.status_code == 200, r.text
png = r.content
# PNG header + IHDR size
import struct
assert png[:8] == b"\x89PNG\r\n\x1a\n"
width, height = struct.unpack(">II", png[16:24])
print(f"PNG individual OK — {width}x{height}, {len(png)} bytes")

# 2. Export ZIP masivo
r = requests.post(f"{BASE}/api/export/all", json={
    "destination": "Machu Picchu",
    "count": 3,
    "language": "es",
    "template_id": "cinco-datos",
    "format_id": "square",
    "cards": cards,
})
assert r.status_code == 200, r.text
zf = zipfile.ZipFile(io.BytesIO(r.content))
names = zf.namelist()
print(f"ZIP OK — archivos: {names}")
copy = zf.read("copy.txt").decode("utf-8")
assert "TARJETA 1" in copy and "Machu Picchu" in copy
print(f"copy.txt OK — {len(copy)} chars")
png_bytes = zf.read(names[0])
assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
print("PNG dentro del ZIP OK")
