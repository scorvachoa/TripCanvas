import json
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response

from models.project import Project, ProjectCreate, ProjectUpdate
from services import local_storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["projects"])


@router.get("/templates")
def list_templates() -> list[dict]:
    from services.template_service import list_templates as _list

    return _list()


@router.get("/templates/{template_id}")
def get_template(template_id: str) -> dict:
    from services.template_service import load_template

    tpl = load_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    return {
        "id": tpl.id,
        "name": tpl.name,
        "category": tpl.category,
        "description": tpl.description,
        "html": tpl.html,
        "css": tpl.css,
    }


@router.post("/projects", status_code=201)
def create_project(payload: ProjectCreate) -> Project:
    return local_storage.create_project(payload)


@router.get("/projects")
def list_projects() -> list[dict]:
    return local_storage.list_projects()


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> Project:
    project = local_storage.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@router.put("/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate) -> Project:
    project = local_storage.update_project(project_id, payload)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str) -> None:
    if not local_storage.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")


@router.get("/projects/{project_id}/download")
def download_project(project_id: str) -> Response:
    data = local_storage.export_project(project_id)
    if not data:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    filename = f"{data.get('name', project_id)}.json"
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/projects/upload", status_code=201)
async def upload_project(file: UploadFile = File(...)) -> Project:
    if not file.filename or not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un .json")
    try:
        content = await file.read(MAX_UPLOAD_SIZE + 1)
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"El archivo excede el tamaño máximo de {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
            )
        data = json.loads(content.decode("utf-8"))
    except HTTPException:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Archivo JSON inválido")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Formato de proyecto inválido")
    return local_storage.import_project(data)
