import json
import re
from typing import Any

from models.content import Card, GenerationResult, ValidationResult


class ValidationError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def extract_json(text: str) -> dict[str, Any] | None:
    """Extrae el primer objeto JSON válido del texto de respuesta."""
    if not text:
        return None

    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _validate_card(card: dict[str, Any], index: int, errors: list[str]) -> None:
    title = str(card.get("title") or "").strip()
    if len(title) > 100:
        errors.append(f"Tarjeta {index + 1}: título demasiado largo ({len(title)} chars).")

    body = str(card.get("body") or "").strip()
    if len(body) > 400:
        errors.append(f"Tarjeta {index + 1}: cuerpo demasiado largo ({len(body)} chars).")

    if not any(
        key in card and str(card.get(key) or "").strip()
        for key in ("title", "body", "question", "myth", "reality", "facts", "answer")
    ):
        errors.append(f"Tarjeta {index + 1}: contenido vacío.")


def validate_response(
    data: dict[str, Any] | None, expected_count: int
) -> ValidationResult:
    errors: list[str] = []

    if data is None:
        return ValidationResult(valid=False, errors=["La respuesta no es JSON válido."])

    cards = data.get("cards")
    if not isinstance(cards, list) or not cards:
        errors.append("La respuesta no contiene tarjetas.")

    if cards:
        if len(cards) != expected_count:
            errors.append(
                f"Se esperaban {expected_count} tarjetas, se recibieron {len(cards)}."
            )
        seen_titles: set[str] = set()
        for i, card in enumerate(cards):
            if not isinstance(card, dict):
                errors.append(f"Tarjeta {i + 1} no es un objeto válido.")
                continue
            _validate_card(card, i, errors)
            title = str(card.get("title") or "").strip().lower()
            if title in seen_titles and title:
                errors.append(f"Título duplicado: '{card.get('title')}'.")
            seen_titles.add(title)

    return ValidationResult(valid=not errors, errors=errors)


def to_generation_result(data: dict[str, Any]) -> GenerationResult:
    cards = []
    for card_data in data.get("cards", []):
        card = Card(
            type=card_data.get("type", "dato_curioso"),
            title=card_data.get("title", ""),
            body=card_data.get("body", ""),
            facts=card_data.get("facts", []) or [],
            question=card_data.get("question", ""),
            answer=card_data.get("answer", ""),
            myth=card_data.get("myth", ""),
            reality=card_data.get("reality", ""),
            options=card_data.get("options", []) or [],
            location=card_data.get("location", ""),
            altitude=card_data.get("altitude", ""),
            source=card_data.get("source", ""),
            image=card_data.get("image"),
            image_query=card_data.get("image_query", ""),
            number=card_data.get("number"),
            extra=card_data.get("extra", {}) or {},
        )
        cards.append(card)
    return GenerationResult(destination=data.get("destination", ""), cards=cards)
