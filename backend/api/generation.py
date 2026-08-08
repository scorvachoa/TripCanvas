import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from gemini.client import RateLimitError
from gemini.content_generator import generate_content
from models.content import GenerateRequest, GenerationResult
from services.rate_limit import rate_limit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["generation"])


@router.post("/generate")
def generate(
    payload: GenerateRequest,
    _limit: None = Depends(rate_limit()),
) -> GenerationResult:
    attempts = 0
    for _ in range(3):
        attempts += 1
        try:
            result = generate_content(payload)
            return result
        except HTTPException:
            raise
        except ValueError as exc:
            logger.warning("Generación inválida: %s", exc)
            raise HTTPException(
                status_code=422,
                detail="No se pudo generar el contenido con la calidad requerida. Inténtalo nuevamente.",
            )
        except RateLimitError as exc:
            logger.error("Límite de cuota en intento %d/3: %s", attempts, exc)
            if attempts >= 3:
                break
            time.sleep(2 * attempts)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error en generación Gemini (intento %d/3): %s", attempts, exc)
            break

    raise HTTPException(
        status_code=502,
        detail="Gemini no respondió. Inténtalo nuevamente.",
    )
