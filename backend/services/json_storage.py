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
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import DATA_DIR

logger = logging.getLogger(__name__)

try:
    import msvcrt  # Windows

    def _lock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_file(f):
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

except ImportError:  # Linux/macOS
    import fcntl

    def _lock_file(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock_file(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


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


def _backup_corrupt(path: Path) -> None:
    """Si el JSON está corrupto, lo respalda con sufijo antes de que se sobrescriba."""
    if not path.exists():
        return
    try:
        backup = path.with_name(f"{path.stem}.corrupt-{int(time.time())}{path.suffix}")
        os.replace(path, backup)
        logger.error(
            "projects.json estaba corrupto. Se respaldó como %s y se iniciará vacío.",
            backup.name,
        )
    except OSError as exc:
        logger.error("No se pudo respaldar projects.json corrupto: %s", exc)


def _load_projects() -> list[dict]:
    if not PROJECTS_FILE.exists():
        return []
    try:
        with open(PROJECTS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("projects", [])
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("No se pudo leer projects.json: %s", exc)
        if isinstance(exc, json.JSONDecodeError):
            _backup_corrupt(PROJECTS_FILE)
        return []


def _save_projects(projects: list[dict]) -> None:
    _atomic_write(PROJECTS_FILE, {"projects": projects})


class _LockedMutation:
    """Contexto que serializa read-modify-write sobre projects.json.

    Adquiere un lock exclusivo sobre el archivo antes de leer, para que las
    operaciones concurrentes (create/update/delete) no se pisen entre sí.
    """

    def __init__(self) -> None:
        self._lock_path = PROJECTS_FILE.with_suffix(".json.lock")
        self._handle = None

    def __enter__(self) -> list[dict]:
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = open(self._lock_path, "a+", encoding="utf-8")
        try:
            _lock_file(self._handle)
        except OSError:
            self._handle.close()
            raise
        return _load_projects()

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            _unlock_file(self._handle)
        finally:
            self._handle.close()


def _locked_mutation():
    return _LockedMutation()


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
    with _locked_mutation() as projects:
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
    with _locked_mutation() as projects:
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
    with _locked_mutation() as projects:
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
