# TripCanvas — AI Travel Content Studio

Herramienta web para crear tarjetas visuales sobre destinos turísticos de Perú usando IA (Google Gemini). El contenido lo genera Gemini; el diseño lo controlan plantillas HTML/CSS independientes.

## Requisitos

- Python 3.11+
- `curl` disponible en el PATH (se usa para llamar a la API de Gemini)
- Una clave de API de Google Gemini

## Instalación

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# 2. Instalar el navegador de Playwright (para exportar PNG)
.venv\Scripts\python -m playwright install chromium

# 3. Configurar la API key
# Copia .env.example a .env y completa GEMINI_API_KEY (o define la variable de entorno)
# Para rotación automática ante límites de cuota, añade más claves numeradas:
#   GEMINI_API_KEY_1=clave2
#   GEMINI_API_KEY_2=clave3
# Se usa primero GEMINI_API_KEY y luego las numeradas en orden.
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
- **Almacenamiento:** archivos JSON (`data/projects.json`, escritura atómica con lock de archivo)
- **Exportación:** Playwright (renderiza el HTML/CSS real a PNG en un directorio temporal por petición)
- **Rate limit:** 10 solicitudes de generación por minuto y por IP (en memoria)

## Estructura

```
backend/
  main.py              # FastAPI, rutas de páginas y montaje del frontend
  config.py            # Configuración desde .env
  gemini/              # Cliente, prompts y generador de contenido (aislado)
  api/                 # Endpoints: generation, projects, export
  models/              # Modelos Pydantic (content, project)
  services/            # export, validation, template, json_storage, rate_limit
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
data/                  # categories.json, projects.json
scripts/               # Utilidades de desarrollo y pruebas
output/                # Exportaciones generadas
```

## API principal

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/generate` | Genera contenido con Gemini (JSON validado) |
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

## Notas de implementación

- Gemini solo devuelve **datos JSON**; nunca HTML/CSS. Contenido y diseño están separados.
- La preview del editor es HTML/CSS real (no una imagen), por lo que la edición se ve en tiempo real.
- Los formatos soportados: Instagram Portrait (1080×1350), Square (1080×1080), Story (1080×1920).
- La exportación usa el HTML renderizado con las plantillas exactamente al tamaño seleccionado. Las imágenes remotas se incrustan en base64 cuando el servidor no puede alcanzarlas (403/hotlink/firewalls).
- Los `template_id` se validan con regex (`^[a-zA-Z0-9_-]+$`) para evitar path traversal.
- `projects.json` usa lock de archivo (msvcrt/fcntl) en operaciones de lectura-modificación-escritura; si el JSON se encuentra corrupto se respalda como `projects.corrupt-<timestamp>.json` antes de continuar.
- El endpoint `/api/generate` está limitado a 10 peticiones por minuto y por IP (en memoria; se reinicia al reiniciar el servidor).

## Pruebas

```bash
# E2E del frontend (requiere servidor corriendo)
.venv\Scripts\python scripts\e2e_test.py

# Flujo completo real (Gemini -> proyecto -> exportación)
.venv\Scripts\python scripts\full_flow_test.py

# Prueba de exportación
.venv\Scripts\python scripts\export_test.py

# CRUD de proyectos contra el servidor
.venv\Scripts\python scripts\json_crud_test.py
```

> Los tests requieren el servidor corriendo. Puedes iniciarlo y probarlo en un solo comando
> (cmd): `scripts\start_server.py 8000` y ejecutar el test; o usar
> `taskkill /F /IM python.exe` para limpiar procesos huérfanos tras las pruebas.