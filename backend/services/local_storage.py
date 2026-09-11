"""Almacenamiento local de proyectos en archivos JSON.

Cada proyecto se guarda como un archivo JSON en data/projects/.
El usuario puede descargar el JSON, editarlo y subirlo de nuevo.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import DATA_DIR
from models.content import Card
from models.project import Project, ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)

PROJECTS_DIR = DATA_DIR / "projects"


def _ensure_dir():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def _project_path(project_id: str) -> Path:
    return PROJECTS_DIR / f"{project_id}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_raw(project_id: str) -> dict | None:
    path = _project_path(project_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Error leyendo proyecto %s: %s", project_id, exc)
        return None


def _save_raw(project_id: str, data: dict) -> None:
    _ensure_dir()
    path = _project_path(project_id)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Proyecto guardado: %s", path.name)


def _data_to_project(data: dict) -> Project:
    return Project(
        id=data["id"],
        name=data.get("name", ""),
        destination=data.get("destination", ""),
        template=data.get("template", "dato-curioso"),
        format=data.get("format", "instagram_portrait"),
        cards=[Card(**c) for c in data.get("cards", [])],
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
    )


def list_projects() -> list[dict]:
    _ensure_dir()
    projects = []
    for path in sorted(PROJECTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        data = _load_raw(path.stem)
        if data:
            projects.append({
                "id": data["id"],
                "name": data.get("name", ""),
                "destination": data.get("destination", ""),
                "template": data.get("template", "dato-curioso"),
                "format": data.get("format", "instagram_portrait"),
                "cards_count": len(data.get("cards", [])),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
            })
    return projects


def get_project(project_id: str) -> Project | None:
    data = _load_raw(project_id)
    if not data:
        return None
    return _data_to_project(data)


def create_project(payload: ProjectCreate) -> Project:
    project_id = uuid.uuid4().hex[:12]
    now = _now_iso()
    data = {
        "id": project_id,
        "name": payload.name,
        "destination": payload.destination,
        "template": payload.template,
        "format": payload.format,
        "cards": [c.model_dump() for c in payload.cards],
        "created_at": now,
        "updated_at": now,
    }
    _save_raw(project_id, data)
    return _data_to_project(data)


def update_project(project_id: str, payload: ProjectUpdate) -> Project | None:
    data = _load_raw(project_id)
    if not data:
        return None
    if payload.name is not None:
        data["name"] = payload.name
    if payload.destination is not None:
        data["destination"] = payload.destination
    if payload.template is not None:
        data["template"] = payload.template
    if payload.format is not None:
        data["format"] = payload.format
    if payload.cards is not None:
        data["cards"] = [c.model_dump() for c in payload.cards]
    data["updated_at"] = _now_iso()
    _save_raw(project_id, data)
    return _data_to_project(data)


def delete_project(project_id: str) -> bool:
    path = _project_path(project_id)
    if not path.exists():
        return False
    path.unlink()
    logger.info("Proyecto eliminado: %s", path.name)
    return True


def export_project(project_id: str) -> dict | None:
    return _load_raw(project_id)


def import_project(data: dict) -> Project:
    project_id = data.get("id") or uuid.uuid4().hex[:12]
    now = _now_iso()
    data["id"] = project_id
    if not data.get("created_at"):
        data["created_at"] = now
    data["updated_at"] = now
    _save_raw(project_id, data)
    return _data_to_project(data)
