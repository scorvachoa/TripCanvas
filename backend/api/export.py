import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from models.content import Card, GenerateRequest
from services.export_service import export_card_png, export_cards_zip, render_card_html
from services.rate_limit import _check_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["export"])


class ExportRequest(Card):
    destination: str = ""
    template_id: str = "dato-curioso"
    format_id: str = "instagram_portrait"
    design: dict = {}
    compress: bool = False


class ExportBulkRequest(GenerateRequest):
    template_id: str = "dato-curioso"
    format_id: str = "instagram_portrait"
    cards: list[Card] = []
    design: dict = {}
    compress: bool = False


def _cleanup_tmp(path: Path) -> None:
    try:
        shutil.rmtree(path, ignore_errors=True)
    except OSError:
        pass


@router.post("/preview")
def preview_card(payload: ExportRequest) -> HTMLResponse:
    html = render_card_html(
        payload,
        payload.template_id,
        destination=payload.destination,
        format_id=payload.format_id,
        design=payload.design,
    )
    return HTMLResponse(html)


@router.post("/export")
async def export_card(
    payload: ExportRequest,
    background: BackgroundTasks,
    request: Request,
) -> FileResponse:
    if payload.compress:
        _check_rate_limit(request, max_requests=30)

    tmp_dir = Path(tempfile.mkdtemp(prefix="tc_export_"))
    try:
        path = await export_card_png(
            payload,
            payload.template_id,
            destination=payload.destination,
            format_id=payload.format_id,
            design=payload.design,
            output_dir=tmp_dir,
            compress=payload.compress,
        )
    except Exception as exc:
        logger.error("Error exportando tarjeta: %s", exc)
        _cleanup_tmp(tmp_dir)
        raise HTTPException(status_code=500, detail="No se pudo exportar la tarjeta.")

    background.add_task(_cleanup_tmp, tmp_dir)
    return FileResponse(path, media_type="image/png", filename=path.name)


@router.post("/export/all")
async def export_all(
    payload: ExportBulkRequest,
    background: BackgroundTasks,
    request: Request,
) -> FileResponse:
    if not payload.cards:
        raise HTTPException(status_code=422, detail="No hay tarjetas para exportar.")

    if payload.compress:
        _check_rate_limit(request, max_requests=30)

    tmp_dir = Path(tempfile.mkdtemp(prefix="tc_export_"))
    try:
        path = await export_cards_zip(
            payload.cards,
            payload.template_id,
            destination=payload.destination or "tripcanvas",
            format_id=payload.format_id,
            design=payload.design,
            output_dir=tmp_dir,
            compress=payload.compress,
        )
    except Exception as exc:
        logger.error("Error exportando ZIP: %s", exc)
        _cleanup_tmp(tmp_dir)
        raise HTTPException(status_code=500, detail="No se pudieron exportar las tarjetas.")

    background.add_task(_cleanup_tmp, tmp_dir)
    return FileResponse(path, media_type="application/zip", filename=path.name)
