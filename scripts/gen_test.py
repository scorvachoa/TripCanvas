import sys
import time

sys.path.insert(0, "backend")

from gemini.content_generator import generate_content
from models.content import GenerateRequest

for cat in ["cinco_datos", "mito_realidad", "guia_rapida"]:
    t = time.time()
    r = generate_content(GenerateRequest(destination="Cusco", category=cat, count=2, language="es"))
    c = r.cards[0]
    print(
        f"== {cat} en {time.time()-t:.1f}s | facts={len(c.facts)} "
        f"| myth={bool(c.myth)} | reality={bool(c.reality)} | title={(c.title or '')[:40]}"
    )
    for f in c.facts[:3]:
        print("   fact:", f if isinstance(f, str) else f)
