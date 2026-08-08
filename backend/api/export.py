import logging
import shutil
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
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


def _cleanup_tmp(path: Path) -> None:
    """Borra el directorio temporal creado para la exportación."""
    try:
        shutil.rmtree(path, ignore_errors=True)
    except OSError:
        pass


@router.post("/export")
async def export_card(payload: ExportRequest, background: BackgroundTasks) -> FileResponse:
    tmp_dir = Path(tempfile.mkdtemp(prefix="tc_export_"))
    try:
        path = await export_card_png(
            payload,
            payload.template_id,
            destination=payload.destination,
            format_id=payload.format_id,
            design=payload.design,
            output_dir=tmp_dir,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Error exportando tarjeta: %s", exc)
        _cleanup_tmp(tmp_dir)
        raise HTTPException(status_code=500, detail="No se pudo exportar la tarjeta.")

    background.add_task(_cleanup_tmp, tmp_dir)
    return FileResponse(
        path,
        media_type="image/png",
        filename=path.name,
    )


@router.post("/export/all")
async def export_all(payload: ExportBulkRequest, background: BackgroundTasks) -> FileResponse:
    if not payload.cards:
        raise HTTPException(status_code=422, detail="No hay tarjetas para exportar.")

    tmp_dir = Path(tempfile.mkdtemp(prefix="tc_export_"))
    try:
        path = await export_cards_zip(
            payload.cards,
            payload.template_id,
            destination=payload.destination or "tripcanvas",
            format_id=payload.format_id,
            design=payload.design,
            output_dir=tmp_dir,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Error exportando ZIP: %s", exc)
        _cleanup_tmp(tmp_dir)
        raise HTTPException(status_code=500, detail="No se pudieron exportar las tarjetas.")

    background.add_task(_cleanup_tmp, tmp_dir)
    return FileResponse(
        path,
        media_type="application/zip",
        filename=path.name,
    )
