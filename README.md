# TripCanvas — AI Travel Content Studio

Herramienta web para crear tarjetas visuales sobre destinos turísticos usando IA (Google Gemini). El contenido lo genera Gemini; el diseño lo controlan plantillas HTML/CSS independientes. Los proyectos se guardan como archivos JSON locales (sin base de datos).

## Requisitos

- Python 3.12+
- Una clave de API de Google Gemini
- Una API key de Pexels (gratuita en https://www.pexels.com/api/) para las fotos automáticas del destino
- Una API key de Tinify/TinyPNG (opcional, https://tinypng.com/developers) para comprimir los PNG al exportar (500 compresiones gratis al mes)

## Instalación

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# 2. Instalar el navegador de Playwright (para exportar PNG)
.venv\Scripts\python -m playwright install chromium

# 3. Configurar credenciales
# Copia .env.example a .env y completa las API keys:
#   GEMINI_API_KEY=tu_clave
#   PEXELS_API_KEY=tu_clave (fotos del destino)
#   TINIFY_API_KEY=tu_clave (compresión PNG, opcional)
# Para rotación automática ante límites de cuota, añade más claves numeradas:
#   GEMINI_API_KEY_1=clave2
#   GEMINI_API_KEY_2=clave3
# Se usa primero GEMINI_API_KEY y luego las numeradas en orden.
```

## Ejecución

```bash
# Inicia el backend en http://localhost:8080
.venv\Scripts\python -m uvicorn main:app --app-dir backend --port 8080
```

Abre `http://localhost:8080` en tu navegador.

## Frontend: páginas y rutas

La aplicación es **multi-página** (HTML separados servidos por FastAPI):

| Ruta | Archivo | Contenido |
|------|---------|-----------|
| `/` | `frontend/index.html` | Home informativo: hero, características, generación rápida y proyectos recientes |
| `/crear` | `frontend/crear.html` | Formulario de creación + subir proyecto JSON |
| `/plantillas` | `frontend/plantillas.html` | Galería de plantillas con preview de ejemplo |
| `/editor` | `frontend/editor.html` | Editor completo (contenido + preview + diseño + exportar) |

## Stack

- **Frontend:** HTML, CSS vanilla (sin frameworks), JavaScript vanilla; notificaciones con **SweetAlert2** (CDN)
- **Backend:** Python + FastAPI
- **IA:** Google Gemini (`backend/gemini/`)
- **HTTP:** httpx (cliente para API de Gemini)
- **Fotos del destino:** Pexels (`services/pexels_service.py`)
- **Compresión PNG:** Tinify/TinyPNG (`services/tinify_service.py`, opcional)
- **Almacenamiento:** Archivos JSON locales en `data/projects/` (sin base de datos)
- **Exportación:** Playwright (renderiza HTML/CSS a PNG)
- **Rate limit:** 10 solicitudes de generación, 30 de exportación por minuto y por IP

## Estructura

```
backend/
  main.py              # FastAPI, rutas de páginas y lifespan
  config.py            # Configuración desde .env
  gemini/              # Cliente (httpx) y prompts de Gemini
  api/                 # Endpoints: generation, projects, export, preview
  models/              # Modelos Pydantic (content, project)
  services/
    export_service.py      # Orquestación de exportación PNG/ZIP
    image_embedder.py      # Descarga y embedding de imágenes (anti-SSRF)
    browser_manager.py     # Gestión del navegador Chromium (Playwright)
    validation_service.py  # Validación de respuestas de Gemini
    template_service.py    # Carga de plantillas HTML/CSS
    local_storage.py       # Almacenamiento de proyectos en JSON
    pexels_service.py      # Búsqueda de fotos en Pexels
    tinify_service.py      # Compresión de imágenes con Tinify
    rate_limit.py          # Rate limiting en memoria
tests/                 # Unit tests
frontend/
  index.html           # Home informativo
  crear.html           # Creación + subir proyecto
  plantillas.html      # Galería de plantillas
  editor.html          # Editor (contenido, preview, diseño, exportar)
  css/styles.css       # CSS unificado (sin Tailwind)
  js/                  # api, icons, preview, templates, generator, editor, export, app
  favicon.svg
templates/             # Plantillas independientes (html + css + config.json)
  dato-curioso/        # dato-curioso/, cinco-datos/, mito-realidad/, quiz/, ...
  ... (15 plantillas en total)
data/
  projects/            # Proyectos guardados como JSON
pyproject.toml         # Configuración de pytest y mypy
```

## API principal

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado del servidor |
| POST | `/api/generate` | Genera contenido con Gemini; `template_id` elige la plantilla |
| GET | `/api/templates` | Lista plantillas |
| GET | `/api/templates/{id}` | HTML/CSS de una plantilla |
| POST | `/api/projects` | Crear proyecto (guarda como JSON) |
| GET | `/api/projects` | Listar proyectos |
| GET | `/api/projects/{id}` | Obtener proyecto |
| PUT | `/api/projects/{id}` | Actualizar proyecto |
| DELETE | `/api/projects/{id}` | Eliminar proyecto |
| GET | `/api/projects/{id}/download` | Descargar proyecto como JSON |
| POST | `/api/projects/upload` | Subir proyecto JSON para importar (máx. 5 MB) |
| POST | `/api/preview` | Render de una tarjeta como HTML (para el editor) |
| POST | `/api/export` | Exportar una tarjeta a PNG |
| POST | `/api/export/all` | Exportar ZIP con PNGs + copy.txt |

## Seguridad

- **Anti-SSRF:** Las imágenes externas solo se descargan de dominios permitidos (Pexels, Unsplash).
- **Límite de upload:** Los proyectos importados no pueden superar 5 MB.
- **Rate limiting:** Protección contra abuso en endpoints de generación y exportación.
- **Sanitización HTML/CSS:** Todo el contenido se escapa para prevenir XSS.
- **Validación de plantillas:** Los IDs de plantilla solo aceptan caracteres alfanuméricos, guiones y guiones bajos.

## Notas de implementación

- **Sin base de datos:** los proyectos se guardan como archivos JSON individuales en `data/projects/`. Cada archivo contiene el proyecto completo (cards, diseño, plantilla, etc.).
- **Async/await:** Los endpoints de generación y exportación son async. Las operaciones pesadas (Gemini, Playwright) se ejecutan en threads separados via `asyncio.to_thread()`.
- **Fotos automáticas del destino:** Gemini propone una búsqueda por tarjeta (`image_query`) y el backend descarga una foto real desde Pexels. Sin `PEXELS_API_KEY` la tarjeta se guarda sin foto, sin romper el lote.
- **Compresión Tinify:** al exportar, con `compress: true` el PNG pasa por Tinify. Es best-effort: sin `TINIFY_API_KEY` o con error, se conserva el PNG original.
- **Exportación PNG:** Playwright renderiza el HTML/CSS real a PNG en un directorio temporal por petición. El navegador se reutiliza entre peticiones para mayor rendimiento.
- **Modelo Fact:** Los datos de las tarjetas soportan dos formatos: strings simples o objetos `FactItem` con `label` y `value`.

## Despliegue en Render

El repo incluye `Dockerfile`, `.dockerignore` y `render.yaml`.

1. **Crea un Web Service en Render** desde el repo (runtime Docker) o conecta el Blueprint con `render.yaml`.
2. **Variables de entorno** (dashboard de Render o `render.yaml`):
   - `GEMINI_API_KEY` (requerida)
   - `PEXELS_API_KEY` (opcional, fotos automáticas)
   - `TINIFY_API_KEY` (opcional, compresión PNG)
3. El health check usa `/healthz`. Render inyecta `$PORT`.
4. Los proyectos se guardan en el filesystem del contenedor (efímero en Render). Para persistencia, usar un volumen o exportar proyectos regularmente.

## Pruebas

```bash
# Unit tests (sin servidor ni API key)
python -m pytest tests/ -x -q

# Type checking
mypy backend --ignore-missing-imports

# Linting
pyflakes backend tests
```
