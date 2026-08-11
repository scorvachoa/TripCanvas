# TripCanvas — AI Travel Content Studio

Herramienta web para crear tarjetas visuales sobre destinos turísticos de Perú usando IA (Google Gemini). El contenido lo genera Gemini; el diseño lo controlan plantillas HTML/CSS independientes.

## Requisitos

- Python 3.11+
- `curl` disponible en el PATH (se usa para llamar a la API de Gemini)
- Una clave de API de Google Gemini
- Una API key de Pexels (gratuita en https://www.pexels.com/api/) para las fotos automáticas del destino
- Una base de datos MySQL (p. ej. Aiven for MySQL) con un usuario y password

## Instalación

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# 2. Instalar el navegador de Playwright (para exportar PNG)
.venv\Scripts\python -m playwright install chromium

# 3. Configurar credenciales
# Copia .env.example a .env y completa GEMINI_API_KEY y las variables MYSQL_*:
#   GEMINI_API_KEY=tu_clave
#   MYSQL_HOST=host.l.aivencloud.com
#   MYSQL_PORT=10379
#   MYSQL_USER=avnadmin
#   MYSQL_PASSWORD=tu_password
#   MYSQL_DB=defaultdb
# Para rotación automática ante límites de cuota, añade más claves numeradas:
#   GEMINI_API_KEY_1=clave2
#   GEMINI_API_KEY_2=clave3
# Se usa primero GEMINI_API_KEY y luego las numeradas en orden.
# Pexels (fotos del destino): PEXELS_API_KEY=tu_clave
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
| `/crear` | `frontend/crear.html` | Formulario de generación (2 columnas: formulario + guía de categorías) |
| `/proyectos` | `frontend/proyectos.html` | Lista de proyectos guardados (editar/eliminar) |
| `/plantillas` | `frontend/plantillas.html` | Galería de plantillas (se abre el editor con la plantilla elegida) |
| `/editor` | `frontend/editor.html` | Editor completo (contenido + preview + diseño) |

- La nav es responsive: menú hamburguesa en pantallas ≤ 860px.
- Las páginas comparten header y footer; el estado del editor se pasa por URL (`?project=`, `?template=`) o por un borrador en `sessionStorage`.

## Stack

- **Frontend:** HTML, CSS y JavaScript vanilla (sin frameworks)
- **Backend:** Python + FastAPI
- **IA:** Google Gemini (módulo aislado en `backend/gemini/`)
- **Fotos del destino:** Pexels (`services/pexels_service.py`); Gemini propone la búsqueda por tarjeta
- **Almacenamiento:** MySQL (Aiven) vía PyMySQL con pool de conexiones; la tabla `projects` se crea automáticamente al arrancar
- **Exportación:** Playwright (renderiza el HTML/CSS real a PNG en un directorio temporal por petición)
- **Rate limit:** 10 solicitudes de generación y 5 de exportación por minuto y por IP (en memoria)

## Estructura

```
backend/
  main.py              # FastAPI, rutas de páginas y montaje del frontend
  config.py            # Configuración desde .env
  gemini/              # Cliente, prompts y generador de contenido (aislado)
  api/                 # Endpoints: generation, projects, export
  models/              # Modelos Pydantic (content, project)
  services/            # export, validation, template, mysql_storage, pexels_service, rate_limit
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
data/                  # categories.json
scripts/               # Utilidades de desarrollo, pruebas y backup
output/                # Exportaciones generadas y backups (backups/projects-<fecha>.json)
```

## API principal

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado del servidor y de la conexión a MySQL (`database: ok` o HTTP 503) |
| POST | `/api/generate` | Genera contenido con Gemini (JSON validado); `with_images` opcional para fotos del destino |
| GET | `/api/categories` | Lista categorías |
| GET | `/api/templates` | Lista plantillas |
| GET | `/api/templates/{id}` | HTML/CSS de una plantilla |
| POST | `/api/projects` | Crear proyecto |
| GET | `/api/projects` | Listar proyectos |
| GET | `/api/projects/{id}` | Obtener proyecto |
| PUT | `/api/projects/{id}` | Actualizar proyecto |
| DELETE | `/api/projects/{id}` | Eliminar proyecto |
| POST | `/api/export` | Exportar una tarjeta a PNG (1080×1350 por defecto) |
| POST | `/api/export/all` | Exportar ZIP con PNGs + `copy.txt` |
| POST | `/api/preview` | Render de una tarjeta como HTML (lo usa el editor) |

## Notas de implementación

- Gemini solo devuelve **datos JSON**; nunca HTML/CSS. Contenido y diseño están separados.
- **Fotos automáticas del destino:** con el toggle "Incluir foto" activado, Gemini propone una búsqueda corta por tarjeta (`image_query`) y el backend descarga una foto real desde Pexels (`services/pexels_service.py`) guardando su URL en `card.image`. La foto se incrusta en base64 al renderizar. Sin `PEXELS_API_KEY` (o si una búsqueda falla) la tarjeta se guarda sin foto, sin romper el lote. Hay un límite de 8 fotos por lote para cuidar la cuota gratuita de Pexels (~200 búsquedas/mes).
- La preview del editor es HTML/CSS real y la genera el **backend** (`POST /api/preview`) con el mismo motor que la exportación, de modo que el preview y el PNG final nunca divergen.
- Los formatos soportados: Instagram Portrait (1080×1350), Square (1080×1080), Story (1080×1920).
- La exportación reutiliza una única instancia de Chromium (Playwright) entre peticiones; las imágenes remotas se incrustan en base64 (con caché) cuando el servidor no puede alcanzarlas (403/hotlink/firewalls).
- Los `template_id` se validan con regex (`^[a-zA-Z0-9_-]+$`) para evitar path traversal.
- Los proyectos se guardan en MySQL (`services/mysql_storage.py`); un **pool de conexiones** acotado (máx. 5, `queue.Queue`) evita el coste del handshake TLS por petición. Al obtener una conexión se verifica que siga viva (`SELECT 1`) y se recrea si el servidor la dejó caer; las conexiones que no caben en el pool se cierran. La tabla `projects` se crea con `CREATE TABLE IF NOT EXISTS` en el arranque.
- `/api/health` comprueba la conexión a MySQL y devuelve `{"status":"ok","database":"ok"}` (o HTTP 503 si la BD no responde); el pool se cierra limpio al apagar el servidor.
- **Backups:** `scripts\backup_db.py` exporta todos los proyectos a `output\backups\projects-<fecha>.json` (columnas completas) y permite restaurarlos con `--restore` (upsert, seguro de re-ejecutar). `output/` está en `.gitignore`, así que los backups no se suben al repositorio.
- Si el servidor no puede conectar con MySQL al arrancar, se registra un error claro y el proceso se detiene (fail-fast).
- El endpoint `/api/generate` está limitado a 10 peticiones por minuto y por IP; los endpoints de exportación (`/api/export`, `/api/export/all`) a 5 (en memoria; se reinicia al reiniciar el servidor).

## Despliegue en Render

El repo incluye `Dockerfile`, `.dockerignore` y `render.yaml` (Blueprint).

1. **Aiven**: en la consola de Aiven (Service settings → Allowed IP addresses) añade `0.0.0.0/0` para permitir conexiones desde Render (sus IPs no son fijas).
2. **Crea un Web Service en Render** desde el repo (runtime Docker) o conecta el Blueprint con `render.yaml`.
3. **Variables de entorno** (dashboard de Render o `render.yaml`):
   - `GEMINI_API_KEY`, `GEMINI_API_KEY_1` (opcional, rotación), `PEXELS_API_KEY`, `MYSQL_PASSWORD`
   - `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_DB`
   - SSL es **opcional**: en local la conexión funciona sin CA (Aiven no lo exige). Si quieres verificar el certificado, define `MYSQL_SSL_CA_B64` con el CA de tu proyecto (consola Aiven → Overview → CA Certificate) en base64; el backend lo decodifica a un archivo temporal al arrancar.
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