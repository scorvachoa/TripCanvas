import logging
from pathlib import Path

from config import DATA_DIR
from gemini.client import GeminiClient, get_client
from gemini.prompts import build_correction_prompt, build_generation_prompt
from models.content import Card, GenerateRequest, GenerationResult
from services.validation_service import (
    extract_json,
    to_generation_result,
    validate_response,
)

logger = logging.getLogger(__name__)

MAX_CORRECTIONS = 2


def load_destinations_data() -> str:
    """Carga data/destinations.json y lo convierte a texto de referencia para Gemini."""
    path = Path(DATA_DIR) / "destinations.json"
    if not path.exists():
        return ""
    try:
        import json

        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo cargar destinations.json: %s", exc)
        return ""


def generate_content(
    request: GenerateRequest, client: GeminiClient | None = None
) -> GenerationResult:
    client = client or get_client()
    references = load_destinations_data()

    prompt = build_generation_prompt(
        destination=request.destination,
        category=request.category,
        count=request.count,
        language=request.language,
        destinations_data=references,
    )

    raw = client.generate(prompt, temperature=0.8)
    data = extract_json(raw)

    validation = validate_response(data, expected_count=request.count)
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
        validation = validate_response(data, expected_count=request.count)
        corrections += 1

    if not validation.valid:
        raise ValueError("; ".join(validation.errors))

    result = to_generation_result(data)
    _apply_numbering(result)
    _apply_types(result, request.category)
    return result


def _apply_numbering(result: GenerationResult) -> None:
    for i, card in enumerate(result.cards):
        card.number = i + 1


def _apply_types(result: GenerationResult, category: str) -> None:
    """Asegura que todas las tarjetas tengan el tipo de la categoría solicitada."""
    for card in result.cards:
        if not card.type or card.type == "dato_curioso":
            card.type = category
