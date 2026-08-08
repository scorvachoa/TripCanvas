from pydantic import BaseModel


class Destination(BaseModel):
    id: str
    name: str
    region: str = ""
    country: str = "Perú"
    keywords: list[str] = []
    image_query: str = ""
