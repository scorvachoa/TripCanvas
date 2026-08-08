from pydantic import BaseModel, Field
from typing import Any, Optional

from models.content import Card


class Project(BaseModel):
    id: str
    name: str
    destination: str = ""
    template: str = "dato-curioso"
    format: str = "instagram_portrait"
    cards: list[Card] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    destination: str = ""
    template: str = "dato-curioso"
    format: str = "instagram_portrait"
    cards: list[Card] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    destination: Optional[str] = None
    template: Optional[str] = None
    format: Optional[str] = None
    cards: Optional[list[Card]] = None
