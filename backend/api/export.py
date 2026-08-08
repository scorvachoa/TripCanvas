import logging
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from models.content import Card, GenerateRequest
from services.export_service import export_card_png, export_cards_zip

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["export"])


class ExportRequest(Card):
    destination: str = ""
    template_id: str = "dato-curioso"
    format_id: str = "instagram_portrait"
    design: dict = {}


class ExportBulkRequest(GenerateRequest):
    template_id: str = "dato-curioso"
    format_id: str = "instagram_portrait"
    cards: list[Card] = []
    design: dict = {}


@router.post("/export")
async def export_card(payload: ExportRequest) -> FileResponse:
    try:
        path = await export_card_png(
            payload,
            payload.template_id,
            destination=payload.destination,
            format_id=payload.format_id,
            design=payload.design,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Error exportando tarjeta: %s", exc)
        raise HTTPException(status_code=500, detail="No se pudo exportar la tarjeta.")

    return FileResponse(
        path,
        media_type="image/png",
        filename=path.name,
    )


@router.post("/export/all")
async def export_all(payload: ExportBulkRequest) -> FileResponse:
    if not payload.cards:
        raise HTTPException(status_code=422, detail="No hay tarjetas para exportar.")

    try:
        path = await export_cards_zip(
            payload.cards,
            payload.template_id,
            destination=payload.destination or "tripcanvas",
            format_id=payload.format_id,
            design=payload.design,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Error exportando ZIP: %s", exc)
        raise HTTPException(status_code=500, detail="No se pudieron exportar las tarjetas.")

    return FileResponse(
        path,
        media_type="application/zip",
        filename=path.name,
    )
