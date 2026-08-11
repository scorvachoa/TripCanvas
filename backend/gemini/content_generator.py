import logging

from config import PEXELS_API_KEY
from gemini.client import GeminiClient, get_client
from gemini.prompts import build_correction_prompt, build_generation_prompt
from models.content import GenerateRequest, GenerationResult
from services.pexels_service import search_photo_urls
from services.validation_service import (
    extract_json,
    to_generation_result,
    validate_response,
)

logger = logging.getLogger(__name__)

MAX_CORRECTIONS = 2
# Límite de fotos obtenidas por lote: protege la cuota gratuita de Pexels
# (~200 búsquedas/mes) si el usuario pide muchas tarjetas.
MAX_IMAGE_GENERATIONS = 8


def generate_content(
    request: GenerateRequest, client: GeminiClient | None = None
) -> GenerationResult:
    client = client or get_client()

    prompt = build_generation_prompt(
        destination=request.destination,
        category=request.category,
        count=request.count,
        language=request.language,
    )

    raw = client.generate(prompt, temperature=0.8)
    data = extract_json(raw)

    validation = validate_response(data, expected_count=request.count, category=request.category)
    corrections = 0

    while not validation.valid and corrections < MAX_CORRECTIONS:
        correction_prompt = build_correction_prompt(
            raw_response=raw,
            validation_errors=validation.errors,
            category=request.category,
            count=request.count,
        )
        raw = client.generate(correction_prompt, temperature=0.4)
        data = extract_json(raw)
        validation = validate_response(data, expected_count=request.count, category=request.category)
        corrections += 1

    if not validation.valid:
        raise ValueError("; ".join(validation.errors))

    result = to_generation_result(data)
    _apply_numbering(result)
    _apply_types(result, request.category)
    if request.with_images:
        _apply_destination_images(result)
    return result


def _apply_numbering(result: GenerationResult) -> None:
    for i, card in enumerate(result.cards):
        card.number = i + 1


def _apply_types(result: GenerationResult, category: str) -> None:
    """Asegura que todas las tarjetas tengan el tipo de la categoría solicitada."""
    for card in result.cards:
        if not card.type or card.type == "dato_curioso":
            card.type = category


def _apply_destination_images(result: GenerationResult) -> None:
    """Asigna una foto real del destino a cada tarjeta usando Pexels.

    La búsqueda la propone Gemini en `card.image_query` (o el nombre del
    destino como respaldo). Si falta la API key de Pexels o la búsqueda falla,
    la tarjeta se guarda sin foto: el lote nunca falla completo por las fotos.
    """
    if not PEXELS_API_KEY:
        logger.warning("PEXELS_API_KEY no configurada; tarjetas sin foto automática.")
        return

    for i, card in enumerate(result.cards):
        if i >= MAX_IMAGE_GENERATIONS:
            logger.info(
                "Se alcanzó el máximo de %d fotos; tarjetas restantes sin foto.",
                MAX_IMAGE_GENERATIONS,
            )
            break
        query = (card.image_query or result.destination or "").strip()
        try:
            urls = search_photo_urls(query, PEXELS_API_KEY)
            if urls:
                card.image = urls[i % len(urls)]
            else:
                logger.warning("Pexels sin resultados para '%s'.", query)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "No se pudo obtener la foto de la tarjeta %d ('%s'): %s",
                i + 1,
                query,
                exc,
            )
