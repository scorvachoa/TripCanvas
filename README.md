# TripCanvas — AI Travel Content Studio

Herramienta web para crear tarjetas visuales sobre destinos turísticos usando IA (Google Gemini). El contenido lo genera Gemini; el diseño lo controlan plantillas HTML/CSS independientes. Los proyectos se guardan como archivos JSON locales (sin base de datos).

## Requisitos

- Python 3.11+
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
- **Fotos del destino:** Pexels (`services/pexels_service.py`)
- **Compresión PNG:** Tinify/TinyPNG (`services/tinify_service.py`, opcional)
- **Almacenamiento:** Archivos JSON locales en `data/projects/` (sin base de datos)
- **Exportación:** Playwright (renderiza HTML/CSS a PNG)
- **Rate limit:** 10 solicitudes de generación, 5 de exportación y 120 de preview por minuto y por IP

## Estructura

```
backend/
  main.py              # FastAPI, rutas de páginas y lifespan
  config.py            # Configuración desde .env
  gemini/              # Cliente y prompts de Gemini
  api/                 # Endpoints: generation, projects, export, preview
  models/              # Modelos Pydantic (content, project)
  services/            # export, validation, template, local_storage, pexels, tinify
tests/                 # Unit tests (53 tests)
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
| POST | `/api/projects/upload` | Subir proyecto JSON para importar |
| POST | `/api/preview` | Render de una tarjeta como HTML (para el editor) |
| POST | `/api/export` | Exportar una tarjeta a PNG |
| POST | `/api/export/all` | Exportar ZIP con PNGs + copy.txt |

## Notas de implementación

- **Sin base de datos:** los proyectos se guardan como archivos JSON individuales en `data/projects/`. Cada archivo contiene el proyecto completo (cards, diseño, plantilla, etc.).
- **Edición inline en preview:** al hacer click en cualquier texto de la tarjeta (título, descripción, datos, opciones, etc.) se abre un modal para editarlo directamente. Los campos indexados (datos, opciones, elementos) se mapean automáticamente al array correspondiente del card.
- **Descarga/Subida de proyectos:** el editor tiene botones para descargar el proyecto como JSON y subir un proyecto existente. También se puede subir desde la página de inicio y desde `/crear`.
- **Plantillas con datos de ejemplo:** al abrir una plantilla desde `/plantillas`, el editor se carga con contenido de ejemplo para cada tipo de plantilla (quiz, mito_realidad, cinco_datos, etc.).
- **Preview dinámica:** el contenedor de preview se adapta automáticamente al formato seleccionado (portrait, square, story) sin distorsión.
- **Fotos automáticas del destino:** Gemini propone una búsqueda por tarjeta (`image_query`) y el backend descarga una foto real desde Pexels. Sin `PEXELS_API_KEY` la tarjeta se guarda sin foto, sin romper el lote.
- **Compresión Tinify:** al exportar, con `compress: true` el PNG pasa por Tinify. Es best-effort: sin `TINIFY_API_KEY` o con error, se conserva el PNG original.
- **Exportación PNG:** Playwright renderiza el HTML/CSS real a PNG en un directorio temporal por petición.

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
.venv\Scripts\python -m pytest tests/ -x -q
```
