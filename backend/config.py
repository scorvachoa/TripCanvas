import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


GEMINI_API_KEY = _get("GEMINI_API_KEY")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash")

# Múltiples claves separadas por coma (rotación automática ante 429/quota).
# Se combina con GEMINI_API_KEY si esta también está definida.
GEMINI_API_KEYS = [
    k.strip()
    for k in _get("GEMINI_API_KEYS").split(",")
    if k.strip() and k.strip() != "your_gemini_api_key_here"
]
if GEMINI_API_KEY and GEMINI_API_KEY not in GEMINI_API_KEYS:
    GEMINI_API_KEYS.insert(0, GEMINI_API_KEY)

OUTPUT_DIR = BASE_DIR / _get("OUTPUT_DIR", "output")
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
FRONTEND_DIR = BASE_DIR / "frontend"

CORS_ORIGINS = [
    origin.strip()
    for origin in _get("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
    if origin.strip()
]
