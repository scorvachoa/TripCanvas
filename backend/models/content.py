from pydantic import BaseModel, Field, field_validator
from typing import Any, Optional, Union


class FactItem(BaseModel):
    """Elemento de dato con etiqueta y valor (para comparativas, guías, etc.)."""
    label: str = ""
    value: str = ""


Fact = Union[str, FactItem]


def _coerce_fact(v: Any) -> Fact:
    """Convierte un valor crudo a un Fact válido (str o FactItem)."""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return FactItem(**v)
    if isinstance(v, FactItem):
        return v
    return str(v)


class Card(BaseModel):
    type: str = "dato_curioso"
    title: str = ""
    body: str = ""
    facts: list[Fact] = Field(default_factory=list)
    question: str = ""
    answer: str = ""
    myth: str = ""
    reality: str = ""
    options: list[str] = Field(default_factory=list)
    location: str = ""
    altitude: str = ""
    source: str = ""
    image: Optional[str] = None
    image_query: str = ""
    number: Optional[int] = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("facts", mode="before")
    @classmethod
    def _validate_facts(cls, v: list[Any]) -> list[Fact]:
        if not isinstance(v, list):
            return v
        return [_coerce_fact(item) for item in v]


class GenerationResult(BaseModel):
    destination: str = ""
    cards: list[Card] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    destination: str
    template_id: str = "dato-curioso"
    count: int = Field(ge=1, le=20, default=1)
    language: str = "es"
    with_images: bool = True


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
