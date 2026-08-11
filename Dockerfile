# bookworm (Debian 12): soportado por Playwright 1.49. La variante slim actual
# usa Debian trixie, donde `playwright install --with-deps` falla.
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# curl: la app llama a la API de Gemini vía subprocess (curl).
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Playwright instala Chromium y sus dependencias de sistema (--with-deps).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY backend ./backend
COPY frontend ./frontend
COPY templates ./templates
COPY data ./data

EXPOSE 8000

# Render inyecta $PORT; se usa como respaldo si no está definido.
CMD ["sh", "-c", "uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
