# TripCanvas — AI Travel Content Studio

Herramienta web para crear tarjetas visuales sobre destinos turísticos de Perú usando IA (Google Gemini). El contenido lo genera Gemini; el diseño lo controlan plantillas HTML/CSS independientes.

## Requisitos

- Python 3.11+
- `curl` disponible en el PATH (se usa para llamar a la API de Gemini)
- Una clave de API de Google Gemini
- Una API key de Pexels (gratuita en https://www.pexels.com/api/) para las fotos automáticas del destino
- Una API key de Tinify/TinyPNG (opcional, https://tinypng.com/developers) para comprimir los PNG al exportar (500 compresiones gratis al mes)
- Una base de datos PostgreSQL (p. ej. Supabase) con un usuario y password

## Instalación

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# 2. Instalar el navegador de Playwright (para exportar PNG)
.venv\Scripts\python -m playwright install chromium

# 3. Configurar credenciales
# Copia .env.example a .env y completa GEMINI_API_KEY y DATABASE_URL:
#   GEMINI_API_KEY=tu_clave
#   DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-[REGION].pooler.supabase.com:6543/postgres
# Para rotación automática ante límites de cuota, añade más claves numeradas:
#   GEMINI_API_KEY_1=clave2
#   GEMINI_API_KEY_2=clave3
# Se usa primero GEMINI_API_KEY y luego las numeradas en orden.
# Pexels (fotos del destino): PEXELS_API_KEY=tu_clave
# Tinify (compresión opcional al exportar): TINIFY_API_KEY=tu_clave
# La tabla `projects` se crea automáticamente al arrancar el servidor.
```

## Ejecución

```bash
# Inicia el backend en http://localhost:8000 (sirve también el frontend)
.venv\Scripts\python -m uvicorn main:app --app-dir backend --port 8000
```

Abre `http://localhost:8000` en tu navegador. El destino se escribe como texto libre (ya no hay lista precargada de destinos).

## Frontend: páginas y rutas

La aplicación es **multi-página** (HTML separados servidos por FastAPI):

| Ruta | Archivo | Contenido |
|------|---------|-----------|
| `/` | `frontend/index.html` | Home informativo: hero, características, cómo funciona, generación rápida y proyectos recientes |
| `/crear` | `frontend/crear.html` | Formulario de generación (destino + plantilla; 2 columnas: formulario + guía de plantillas) |
| `/proyectos` | `frontend/proyectos.html` | Lista de proyectos guardados (editar/eliminar) |
| `/plantillas` | `frontend/plantillas.html` | Galería de plantillas (se abre el editor con la plantilla elegida) |
| `/editor` | `frontend/editor.html` | Editor completo (contenido + preview + diseño) |

- La nav es responsive: menú hamburguesa en pantallas ≤ 860px.
- Las páginas comparten header y footer; el estado del editor se pasa por URL (`?project=`, `?template=`) o por un borrador en `sessionStorage`.

## Stack

- **Frontend:** HTML, CSS y JavaScript vanilla (sin frameworks); notificaciones y diálogos con **SweetAlert2** (CDN)
- **Backend:** Python + FastAPI
- **IA:** Google Gemini (módulo aislado en `backend/gemini/`)
- **Fotos del destino:** Pexels (`services/pexels_service.py`); Gemini propone la búsqueda por tarjeta
- **Compresión PNG:** Tinify/TinyPNG (`services/tinify_service.py`), opcional y best-effort al exportar
- **Almacenamiento:** PostgreSQL (Supabase) vía psycopg con pool de conexiones; la tabla `projects` se crea automáticamente al arrancar
- **Exportación:** Playwright (renderiza el HTML/CSS real a PNG en un directorio temporal por petición)
- **Rate limit:** 10 solicitudes de generación, 5 de exportación y 120 de preview por minuto y por IP (en memoria)

## Estructura

```
backend/
  main.py              # FastAPI, rutas de páginas y montaje del frontend
  config.py            # Configuración desde .env
  gemini/              # Cliente, prompts y generador de contenido (aislado)
  api/                 # Endpoints: generation, projects, export
  models/              # Modelos Pydantic (content, project)
  services/            # export, validation, template, supabase_storage, pexels_service, tinify_service, rate_limit
tests/                 # Unit tests (unittest, sin servidor ni API key)
frontend/
  index.html           # Home informativo
  crear.html           # Generación (2 columnas)
  proyectos.html       # Proyectos guardados
  plantillas.html      # Galería de plantillas
  editor.html          # Editor (contenido, preview, diseño)
  css/                 # main, components, dashboard, pages, editor
  js/                  # api, preview, templates, generator, editor, export, app
  favicon.svg
templates/             # Plantillas independientes (html + css + config.json)
  dato-curioso/        # Fotográfico + moderno
  cinco-datos/         # Editorial + informativo
  mito-realidad/       # Contraste visual
  ... (15 plantillas en total)
data/                  # Datos auxiliares (sin categories.json: la plantilla define el tipo)
scripts/               # Utilidades de desarrollo, pruebas y backup
output/                # Exportaciones generadas y backups (backups/projects-<fecha>.json)
```

## API principal

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado del servidor y de la conexión a MySQL (`database: ok` o HTTP 503) |
| POST | `/api/generate` | Genera contenido con Gemini (JSON validado); `template_id` elige la plantilla/tipo de contenido, `with_images` opcional para fotos del destino |
| GET | `/api/templates` | Lista plantillas |
| GET | `/api/templates/{id}` | HTML/CSS de una plantilla |
| POST | `/api/projects` | Crear proyecto |
| GET | `/api/projects` | Listar proyectos |
| GET | `/api/projects/{id}` | Obtener proyecto |
| PUT | `/api/projects/{id}` | Actualizar proyecto |
| DELETE | `/api/projects/{id}` | Eliminar proyecto |
| POST | `/api/export` | Exportar una tarjeta a PNG (1080×1350 por defecto); `compress: true` la optimiza con Tinify |
| POST | `/api/export/all` | Exportar ZIP con PNGs + `copy.txt`; `compress: true` optimiza los PNG con Tinify |
| POST | `/api/preview` | Render de una tarjeta como HTML (lo usa el editor) |

## Notas de implementación

- Gemini solo devuelve **datos JSON**; nunca HTML/CSS. Contenido y diseño están separados.
- **Fotos automáticas del destino:** con el toggle "Incluir foto" activado, Gemini propone una búsqueda corta por tarjeta (`image_query`) y el backend descarga una foto real desde Pexels (`services/pexels_service.py`) guardando su URL en `card.image`. La foto se incrusta en base64 al renderizar. Sin `PEXELS_API_KEY` (o si una búsqueda falla) la tarjeta se guarda sin foto, sin romper el lote. Hay un límite de 8 fotos por lote para cuidar la cuota gratuita de Pexels (~200 búsquedas/mes).
- La preview del editor es HTML/CSS real y la genera el **backend** (`POST /api/preview`) con el mismo motor que la exportación, de modo que el preview y el PNG final nunca divergen.
- **Notificaciones y diálogos:** el frontend usa **SweetAlert2** (CDN, sin instalar nada) para los toasts y las confirmaciones (exportar comprimido/original, eliminar proyecto).
- **Compresión Tinify:** al exportar el frontend pregunta si quieres comprimir. Con `compress: true` el PNG pasa por Tinify (`services/tinify_service.py`). Es *best-effort*: sin `TINIFY_API_KEY`, con error de red/cuota, o si no hay reducción, se conserva el PNG original. La cuota gratuita es de 500 compresiones/mes.
- Los formatos soportados: Instagram Portrait (1080×1350), Square (1080×1080), Story (1080×1920).
- La exportación reutiliza una única instancia de Chromium (Playwright) entre peticiones; las imágenes remotas se incrustan en base64 (con caché) cuando el servidor no puede alcanzarlas (403/hotlink/firewalls).
- Los `template_id` se validan con regex (`^[a-zA-Z0-9_-]+$`) para evitar path traversal.
- Los proyectos se guardan en PostgreSQL/Supabase (`services/supabase_storage.py`); un **pool de conexiones** acotado (máx. 5, `queue.Queue`) evita el coste de abrir una conexión por petición. Al obtener una conexión se verifica que siga viva (`SELECT 1`) y se recrea si el servidor la dejó caer; las conexiones que no caben en el pool se cierran. La tabla `projects` se crea con `CREATE TABLE IF NOT EXISTS` en el arranque.
- `/api/health` comprueba la conexión a PostgreSQL y devuelve `{"status":"ok","database":"ok"}` (o HTTP 503 si la BD no responde); el pool se cierra limpio al apagar el servidor.
- **Backups:** `scripts\backup_db.py` exporta todos los proyectos a `output\backups\projects-<fecha>.json` (columnas completas) y permite restaurarlos con `--restore` (upsert, seguro de re-ejecutar). `output/` está en `.gitignore`, así que los backups no se suben al repositorio.
- Si el servidor no puede conectar con PostgreSQL al arrancar, se registra un error claro y el proceso se detiene (fail-fast).
- El endpoint `/api/generate` está limitado a 10 peticiones por minuto y por IP, la exportación (`/api/export`, `/api/export/all`) a 5 y la preview (`/api/preview`) a 120 (en memoria; se reinician al reiniciar el servidor).

## Despliegue en Render

El repo incluye `Dockerfile`, `.dockerignore` y `render.yaml` (Blueprint).

1. **Supabase**: crea un proyecto en [Supabase](https://supabase.com) y obtén la `DATABASE_URL` desde Settings → Database → Connection string → URI (modo Session o Transaction pooler).
2. **Crea un Web Service en Render** desde el repo (runtime Docker) o conecta el Blueprint con `render.yaml`.
3. **Variables de entorno** (dashboard de Render o `render.yaml`):
   - `GEMINI_API_KEY`, `GEMINI_API_KEY_1` (opcional, rotación), `PEXELS_API_KEY`, `TINIFY_API_KEY` (opcional), `DATABASE_URL`
4. El health check usa `/healthz` (no consulta la BD, evita reinicios en bucle).
5. Render inyecta `$PORT`; el contenedor escucha ahí. `output/` es efímero en Render (los PNG y backups no persisten).

## Pruebas

```bash
# Unit tests (sin servidor ni API key)
.venv\Scripts\python -m unittest discover -s tests

# E2E del frontend (requiere servidor corriendo)
.venv\Scripts\python scripts\e2e_test.py

# Flujo completo real (Gemini -> proyecto -> exportación)
.venv\Scripts\python scripts\full_flow_test.py

# Prueba de exportación
.venv\Scripts\python scripts\export_test.py

# CRUD de proyectos contra el servidor
.venv\Scripts\python scripts\json_crud_test.py

# Backup/restore de proyectos a JSON (crea output/backups/projects-<fecha>.json)
.venv\Scripts\python scripts\backup_db.py
.venv\Scripts\python scripts\backup_db.py --restore output\backups\projects-<fecha>.json
```

> Los tests requieren el servidor corriendo. Puedes iniciarlo y probarlo en un solo comando
> (cmd): `scripts\start_server.py 8000` y ejecutar el test; o usar
> `taskkill /F /IM python.exe` para limpiar procesos huérfanos tras las pruebas.