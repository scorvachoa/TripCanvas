"""Copia de seguridad de los proyectos de MySQL a un archivo JSON local.

Uso:
  .venv\\Scripts\\python scripts\\backup_db.py                # backup a output/backups/
  .venv\\Scripts\\python scripts\\backup_db.py --restore archivo.json

El backup incluye todas las columnas de cada proyecto (id, name, destination,
template, format, cards, created_at, updated_at). El restore hace un upsert
(INSERT ... ON DUPLICATE KEY UPDATE), por lo que es seguro re-ejecutarlo.
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services import mysql_storage  # noqa: E402

BACKUP_DIR = Path("output") / "backups"


def backup(path: Path) -> int:
    projects = mysql_storage.export_all()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": datetime.now().isoformat(),
        "count": len(projects),
        "projects": projects,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(projects)


def restore(path: Path) -> int:
    if not path.exists():
        raise SystemExit(f"No existe el archivo de backup: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    projects = data.get("projects", [])
    return mysql_storage.restore(projects)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup/restore de proyectos MySQL")
    parser.add_argument(
        "--restore",
        metavar="ARCHIVO",
        help="Restaurar proyectos desde un backup JSON en lugar de crear uno",
    )
    parser.add_argument(
        "--out", metavar="RUTA", help="Ruta del backup (por defecto output/backups/projects-<fecha>.json)"
    )
    args = parser.parse_args()

    if args.restore:
        n = restore(Path(args.restore))
        print(f"Restaurados {n} proyectos desde {args.restore}")
        return

    path = Path(args.out) if args.out else BACKUP_DIR / f"projects-{datetime.now():%Y%m%d-%H%M%S}.json"
    n = backup(path)
    print(f"Backup creado con {n} proyectos en {path}")


if __name__ == "__main__":
    main()
