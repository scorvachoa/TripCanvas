import logging

from fastapi import APIRouter, HTTPException

from models.content import Card
from models.project import Project, ProjectCreate, ProjectUpdate
from services import mysql_storage as storage

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


def card_to_dict(card: Card) -> dict:
    """Convierte un Card en el dict que se almacena en JSON."""
    return card.model_dump()


def dict_to_project(data: dict) -> Project:
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


def _get_or_404(project_id: str) -> dict:
    data = storage.get_project(project_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return data


@router.post("/projects", status_code=201)
def create_project(payload: ProjectCreate) -> Project:
    cards = [card_to_dict(card) for card in payload.cards]
    project = storage.create_project(
        name=payload.name,
        destination=payload.destination,
        template=payload.template,
        format_=payload.format,
        cards=cards,
    )
    return dict_to_project(project)


@router.get("/projects")
def list_projects() -> list[dict]:
    return storage.list_projects()


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> Project:
    return dict_to_project(_get_or_404(project_id))


@router.put("/projects/{project_id}")
def update_project(project_id: str, payload: ProjectUpdate) -> Project:
    cards = [card_to_dict(card) for card in payload.cards] if payload.cards is not None else None
    project = storage.update_project(
        project_id,
        name=payload.name,
        destination=payload.destination,
        template=payload.template,
        format_=payload.format,
        cards=cards,
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return dict_to_project(project)


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str) -> None:
    if not storage.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
