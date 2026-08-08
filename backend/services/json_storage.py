"""Almacenamiento en archivos JSON.

Por ahora los proyectos se guardan en data/projects.json (un solo archivo,
escritura atómica). Estructura:

{
  "projects": [
    {
      "id": "...",
      "name": "...",
      "destination": "...",
      "template": "...",
      "format": "...",
      "created_at": "...",
      "updated_at": "...",
      "cards": [ { ...card... } ]
    }
  ]
}
"""
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import DATA_DIR

logger = logging.getLogger(__name__)

PROJECTS_FILE = Path(DATA_DIR) / "projects.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path: Path, data: dict) -> None:
    """Escribe de forma atómica para evitar archivos corruptos."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _load_projects() -> list[dict]:
    if not PROJECTS_FILE.exists():
        return []
    try:
        with open(PROJECTS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("projects", [])
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("No se pudo leer projects.json: %s", exc)
        return []


def _save_projects(projects: list[dict]) -> None:
    _atomic_write(PROJECTS_FILE, {"projects": projects})


def list_projects() -> list[dict]:
    projects = _load_projects()
    projects.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    return [
        {
            "id": p["id"],
            "name": p.get("name", ""),
            "destination": p.get("destination", ""),
            "template": p.get("template", "dato-curioso"),
            "format": p.get("format", "instagram_portrait"),
            "created_at": p.get("created_at", ""),
            "updated_at": p.get("updated_at", ""),
            "cards_count": len(p.get("cards", [])),
        }
        for p in projects
    ]


def get_project(project_id: str) -> dict | None:
    for p in _load_projects():
        if p["id"] == project_id:
            return p
    return None


def create_project(name: str, destination: str, template: str, format_: str, cards: list[dict]) -> dict:
    project = {
        "id": uuid.uuid4().hex,
        "name": name,
        "destination": destination,
        "template": template,
        "format": format_,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "cards": cards,
    }
    projects = _load_projects()
    projects.append(project)
    _save_projects(projects)
    return project


def update_project(
    project_id: str,
    name: str | None = None,
    destination: str | None = None,
    template: str | None = None,
    format_: str | None = None,
    cards: list[dict] | None = None,
) -> dict | None:
    projects = _load_projects()
    for p in projects:
        if p["id"] != project_id:
            continue
        if name is not None:
            p["name"] = name
        if destination is not None:
            p["destination"] = destination
        if template is not None:
            p["template"] = template
        if format_ is not None:
            p["format"] = format_
        if cards is not None:
            p["cards"] = cards
        p["updated_at"] = now_iso()
        _save_projects(projects)
        return p
    return None


def delete_project(project_id: str) -> bool:
    projects = _load_projects()
    remaining = [p for p in projects if p["id"] != project_id]
    if len(remaining) == len(projects):
        return False
    _save_projects(remaining)
    return True


def load_destinations() -> list[dict]:
    path = Path(DATA_DIR) / "destinations.json"
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("No se pudo leer destinations.json: %s", exc)
        return []
