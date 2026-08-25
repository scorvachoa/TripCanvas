"""Almacenamiento en PostgreSQL (Supabase).

Reemplaza el almacenamiento en MySQL (Aiven). La tabla `projects` se crea
automáticamente al arrancar (ver `init_schema`).

Las operaciones usan un pequeño pool de conexiones acotado (POOL_MAXSIZE) que
se valida y reconecta al obtener una conexión, evitando el coste de abrir una
conexión nueva por petición. PostgreSQL resuelve la concurrencia con transacciones.

Esquema de la tabla:

  id          VARCHAR(32)  PK
  name        VARCHAR(200)
  destination TEXT
  template    VARCHAR(64)
  format      VARCHAR(64)
  cards       JSON
  created_at  VARCHAR(64)
  updated_at  VARCHAR(64)
"""
import json
import logging
import queue
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
import psycopg.rows

from config import DATABASE_URL

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id          VARCHAR(32)  NOT NULL,
    name        VARCHAR(200) NOT NULL,
    destination TEXT         NOT NULL,
    template    VARCHAR(64)  NOT NULL DEFAULT 'dato-curioso',
    format      VARCHAR(64)  NOT NULL DEFAULT 'instagram_portrait',
    cards       JSONB        NOT NULL,
    created_at  VARCHAR(64)  NOT NULL,
    updated_at  VARCHAR(64)  NOT NULL,
    PRIMARY KEY (id)
)
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_updated_at ON projects (updated_at)
"""

POOL_MAXSIZE = 5
_POOL_GET_TIMEOUT = 10.0

_pool: queue.Queue | None = None
_pool_lock = threading.Lock()
_pool_total = 0


def _connect():
    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
        options="-c statement_timeout=10000",
    )


def _connection_alive(conn) -> bool:
    """Comprueba que la conexión responde; si no, la cierra."""
    if conn.closed:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass
        return False


def _acquire_connection():
    """Obtiene una conexión del pool, creando una nueva si es necesario."""
    global _pool, _pool_total
    if _pool is None:
        _pool = queue.Queue(maxsize=POOL_MAXSIZE)

    try:
        conn = _pool.get_nowait()
    except queue.Empty:
        with _pool_lock:
            if _pool_total < POOL_MAXSIZE:
                _pool_total += 1
                try:
                    return _connect()
                except Exception:
                    _pool_total -= 1
                    raise
        conn = _pool.get(timeout=_POOL_GET_TIMEOUT)

    if not _connection_alive(conn):
        conn = _connect()
    return conn


def _release_connection(conn) -> None:
    """Devuelve la conexión al pool; la cierra si el pool está lleno o está muerta."""
    if _pool is None:
        return
    try:
        if not conn.closed:
            _pool.put_nowait(conn)
        else:
            conn.close()
    except queue.Full:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass


def close_pool() -> None:
    """Cierra todas las conexiones del pool (llamar al apagar la app)."""
    global _pool, _pool_total
    if _pool is None:
        return
    while True:
        try:
            conn = _pool.get_nowait()
        except queue.Empty:
            break
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass
    _pool = None
    _pool_total = 0


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decode_cards(raw: Any) -> list[dict]:
    """La columna JSON puede llegar como str o ya deserializada según el driver."""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return []
    return []


def _row_to_project(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "destination": row["destination"],
        "template": row["template"],
        "format": row["format"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "cards": _decode_cards(row.get("cards")),
    }


def ping() -> None:
    """Comprueba la conectividad con la base de datos (SELECT 1)."""
    conn = _acquire_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    finally:
        _release_connection(conn)


def init_schema() -> None:
    """Crea la tabla si no existe. Se llama en el arranque de la app."""
    conn = _acquire_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(CREATE_INDEX_SQL)
        conn.commit()
        logger.info("Tabla 'projects' lista en PostgreSQL (Supabase).")
    finally:
        _release_connection(conn)


def list_projects() -> list[dict]:
    conn = _acquire_connection()
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT id, name, destination, template, format, "
                "created_at, updated_at, cards FROM projects ORDER BY updated_at DESC"
            )
            rows = cur.fetchall()
    finally:
        _release_connection(conn)
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "destination": r["destination"],
            "template": r["template"],
            "format": r["format"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "cards_count": len(_decode_cards(r["cards"])),
        }
        for r in rows
    ]


def get_project(project_id: str) -> dict | None:
    conn = _acquire_connection()
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM projects WHERE id=%s", (project_id,))
            row = cur.fetchone()
    finally:
        _release_connection(conn)
    return _row_to_project(row) if row else None


def export_all() -> list[dict]:
    """Devuelve todos los proyectos completos (para backups)."""
    conn = _acquire_connection()
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM projects ORDER BY updated_at DESC")
            rows = cur.fetchall()
    finally:
        _release_connection(conn)
    return [_row_to_project(r) for r in rows]


def create_project(
    name: str,
    destination: str,
    template: str,
    format_: str,
    cards: list[dict],
) -> dict:
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
    conn = _acquire_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO projects (id, name, destination, template, format, "
                "cards, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    project["id"],
                    project["name"],
                    project["destination"],
                    project["template"],
                    project["format"],
                    json.dumps(cards, ensure_ascii=False),
                    project["created_at"],
                    project["updated_at"],
                ),
            )
        conn.commit()
    finally:
        _release_connection(conn)
    return project


def restore(projects: list[dict]) -> int:
    """Inserta o actualiza proyectos (restore de un backup). Devuelve nº de filas."""
    if not projects:
        return 0
    conn = _acquire_connection()
    try:
        with conn.cursor() as cur:
            for p in projects:
                cur.execute(
                    "INSERT INTO projects (id, name, destination, template, format, "
                    "cards, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) "
                    "ON CONFLICT (id) DO UPDATE SET "
                    "name=EXCLUDED.name, destination=EXCLUDED.destination, "
                    "template=EXCLUDED.template, format=EXCLUDED.format, cards=EXCLUDED.cards, "
                    "created_at=EXCLUDED.created_at, updated_at=EXCLUDED.updated_at",
                    (
                        p["id"],
                        p.get("name", ""),
                        p.get("destination", ""),
                        p.get("template", "dato-curioso"),
                        p.get("format", "instagram_portrait"),
                        json.dumps(p.get("cards", []), ensure_ascii=False),
                        p.get("created_at", now_iso()),
                        p.get("updated_at", now_iso()),
                    ),
                )
        conn.commit()
        return len(projects)
    finally:
        _release_connection(conn)


def update_project(
    project_id: str,
    name: str | None = None,
    destination: str | None = None,
    template: str | None = None,
    format_: str | None = None,
    cards: list[dict] | None = None,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    if name is not None:
        sets.append("name=%s")
        params.append(name)
    if destination is not None:
        sets.append("destination=%s")
        params.append(destination)
    if template is not None:
        sets.append("template=%s")
        params.append(template)
    if format_ is not None:
        sets.append("format=%s")
        params.append(format_)
    if cards is not None:
        sets.append("cards=%s")
        params.append(json.dumps(cards, ensure_ascii=False))

    if not sets:
        return get_project(project_id)

    sets.append("updated_at=%s")
    params.append(now_iso())
    params.append(project_id)

    conn = _acquire_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE projects SET {', '.join(sets)} WHERE id=%s", tuple(params)
            )
        conn.commit()
    finally:
        _release_connection(conn)
    return get_project(project_id)


def delete_project(project_id: str) -> bool:
    conn = _acquire_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM projects WHERE id=%s", (project_id,))
            deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        _release_connection(conn)
