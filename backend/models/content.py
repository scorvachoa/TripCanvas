from pydantic import BaseModel, Field
from typing import Any, Optional, Union

Fact = Union[str, dict]


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
