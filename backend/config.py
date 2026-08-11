import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


GEMINI_API_KEY = _get("GEMINI_API_KEY")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash")

# API key de Pexels (gratis en pexels.com/api). Se usa para las fotos
# automáticas del destino cuando el usuario activa "Incluir fotos". Si está
# vacía, las tarjetas se generan sin foto.
PEXELS_API_KEY = _get("PEXELS_API_KEY")

# Claves adicionales numeradas (GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...) para
# rotación automática ante 429/quota. Se usa primero GEMINI_API_KEY y luego
# las numeradas en orden ascendente.
GEMINI_API_KEYS: list[str] = []
if GEMINI_API_KEY:
    GEMINI_API_KEYS.append(GEMINI_API_KEY)
_index = 1
while True:
    numbered = _get(f"GEMINI_API_KEY_{_index}")
    if not numbered:
        break
    if numbered != "your_gemini_api_key_here":
        GEMINI_API_KEYS.append(numbered)
    _index += 1

OUTPUT_DIR = BASE_DIR / _get("OUTPUT_DIR", "output")
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
FRONTEND_DIR = BASE_DIR / "frontend"

# MySQL (Aiven). El backend guarda los proyectos aquí.
MYSQL_HOST = _get("MYSQL_HOST")
MYSQL_PORT = int(_get("MYSQL_PORT", "10379"))
MYSQL_USER = _get("MYSQL_USER", "avnadmin")
MYSQL_PASSWORD = _get("MYSQL_PASSWORD")
MYSQL_DB = _get("MYSQL_DB", "defaultdb")
# Ruta al certificado CA (opcional). Si se define, la conexión usa SSL.
MYSQL_SSL_CA = _get("MYSQL_SSL_CA") or None
# Alternativa para despliegues (Render): el contenido del CA en base64. Los
# entornos PaaS no permiten montar archivos, así que se escribe en un archivo
# temporal al arrancar.
if not MYSQL_SSL_CA:
    import base64
    import tempfile

    _ca_b64 = _get("MYSQL_SSL_CA_B64")
    if _ca_b64:
        _ca_path = Path(tempfile.gettempdir()) / "tripcanvas_ca.pem"
        _ca_path.write_bytes(base64.b64decode(_ca_b64))
        MYSQL_SSL_CA = str(_ca_path)

CORS_ORIGINS = [
    origin.strip()
    for origin in _get("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
    if origin.strip()
]
