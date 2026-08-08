import logging
import time

from fastapi import APIRouter, HTTPException

from gemini.client import RateLimitError
from gemini.content_generator import generate_content
from models.content import GenerateRequest, GenerationResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/generate")
def generate(payload: GenerateRequest) -> GenerationResult:
    attempts = 0
    last_exc: Exception | None = None
    while attempts < 3:
        attempts += 1
        try:
            result = generate_content(payload)
            if not result.cards:
                raise HTTPException(status_code=502, detail="No se pudo generar el contenido.")
            return result
        except ValueError as exc:
            logger.warning("Generación inválida: %s", exc)
            raise HTTPException(
                status_code=422,
                detail="No se pudo generar el contenido con la calidad requerida. Inténtalo nuevamente.",
            )
        except RateLimitError as exc:
            logger.error("Límite de cuota en intento %d/3: %s", attempts, exc)
            last_exc = exc
            if attempts >= 3:
                break
            time.sleep(2 * attempts)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error en generación Gemini (intento %d/3): %s", attempts, exc)
            last_exc = exc
            break

    raise HTTPException(
        status_code=502,
        detail=str(last_exc) if last_exc else "Gemini no respondió. Inténtalo nuevamente.",
    )
