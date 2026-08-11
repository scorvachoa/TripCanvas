import json
import re
from typing import Any

from models.content import Card, GenerationResult, ValidationResult

# Campos requeridos por categoría, alineados con lo que renderizan las plantillas.
# Las claves con '.' referencian subcampos dentro de `extra`.
CATEGORY_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "dato_curioso": ("title", "body"),
    "sabias_que": ("question", "answer"),
    "historia": ("title", "body", "extra.fecha"),
    "mito_realidad": ("title", "myth", "reality"),
    "quiz": ("question", "answer", "options"),
    "comparativa": ("title", "body", "extra.items"),
    "guia_rapida": ("title", "facts"),
    "cinco_datos": ("title", "facts"),
    "consejos": ("title", "facts"),
    "cultura": ("title", "body", "facts"),
    "arquitectura": ("title", "body"),
    "naturaleza": ("title", "body", "facts"),
    "como_llegar": ("title", "facts"),
    "mejor_epoca": ("title", "facts"),
    "informacion_general": ("title", "body", "facts"),
}


def _get_field(card: dict[str, Any], field: str) -> Any:
    """Obtiene un campo de la tarjeta; soporta rutas tipo 'extra.fecha'."""
    if "." in field:
        key, sub = field.split(".", 1)
        value = card.get(key)
        return value.get(sub, "") if isinstance(value, dict) else ""
    return card.get(field)


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


def _validate_category(card: dict[str, Any], category: str, index: int, errors: list[str]) -> None:
    """Comprueba los campos requeridos por la categoría."""
    for field in CATEGORY_REQUIRED_FIELDS.get(category, ()):
        value = _get_field(card, field)
        if field == "options":
            if not isinstance(value, list) or len(value) < 2:
                errors.append(
                    f"Tarjeta {index + 1}: 'quiz' requiere al menos 2 opciones en 'options'."
                )
        elif field == "extra.items":
            if not isinstance(value, list) or not value:
                errors.append(
                    f"Tarjeta {index + 1}: 'comparativa' requiere una lista en 'extra.items'."
                )
        elif field == "facts":
            if not isinstance(value, list) or not value:
                errors.append(
                    f"Tarjeta {index + 1}: la categoría '{category}' requiere datos en 'facts'."
                )
        elif not str(value or "").strip():
            errors.append(
                f"Tarjeta {index + 1}: la categoría '{category}' requiere el campo '{field}'."
            )


def validate_response(
    data: dict[str, Any] | None, expected_count: int, category: str = ""
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
            _validate_category(card, category, i, errors)
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
