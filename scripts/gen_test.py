import sys
import time

sys.path.insert(0, "backend")

from gemini.content_generator import generate_content

for tpl in ["cinco-datos", "mito-realidad", "guia-rapida"]:
    t = time.time()
    r = generate_content(
        destination="Cusco",
        category={"cinco-datos": "cinco_datos", "mito-realidad": "mito_realidad", "guia-rapida": "guia_rapida"}[tpl],
        count=2,
        language="es",
    )
    c = r.cards[0]
    print(
        f"== {tpl} en {time.time()-t:.1f}s | facts={len(c.facts)} "
        f"| myth={bool(c.myth)} | reality={bool(c.reality)} | title={(c.title or '')[:40]}"
    )
    for f in c.facts[:3]:
        print("   fact:", f if isinstance(f, str) else f)
