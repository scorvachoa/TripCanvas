import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api import export, generation, projects
from config import CORS_ORIGINS, FRONTEND_DIR
from services.export_service import _close_browser

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.local_storage import PROJECTS_DIR
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    await _close_browser()


app = FastAPI(title="TripCanvas API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(generation.router)
app.include_router(export.router)


@app.get("/api/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok"})


_PAGE_FILES = {
    "/crear": "crear.html",
    "/plantillas": "plantillas.html",
    "/editor": "editor.html",
}


def _serve_page(filename: str) -> FileResponse:
    return FileResponse(FRONTEND_DIR / filename)


for _path, _file in _PAGE_FILES.items():
    app.get(_path, include_in_schema=False, name="page-" + _file)(lambda f=_file: _serve_page(f))


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
