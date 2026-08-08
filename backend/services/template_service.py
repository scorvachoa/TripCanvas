import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from config import TEMPLATES_DIR

FORMATS = {
    "instagram_portrait": {"name": "Instagram Portrait", "width": 1080, "height": 1350},
    "square": {"name": "Square", "width": 1080, "height": 1080},
    "story": {"name": "Story", "width": 1080, "height": 1920},
}


@dataclass
class Template:
    id: str
    name: str
    category: str
    description: str = ""
    path: Path = field(default=None)  # type: ignore
    html: str = ""
    css: str = ""

    def __post_init__(self) -> None:
        if self.path is not None:
            self._load_files()

    def _load_files(self) -> None:
        html_path = self.path / "template.html"
        css_path = self.path / "template.css"
        if html_path.exists():
            self.html = html_path.read_text(encoding="utf-8")
        if css_path.exists():
            self.css = css_path.read_text(encoding="utf-8")


_TEMPLATE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def is_safe_template_id(template_id: str) -> bool:
    """El id debe ser un nombre de carpeta simple (sin rutas ni separadores)."""
    return bool(template_id) and bool(_TEMPLATE_ID_RE.fullmatch(template_id))


def load_template(template_id: str) -> Template | None:
    if not is_safe_template_id(template_id):
        return None
    template_dir = TEMPLATES_DIR / template_id
    if not template_dir.exists():
        return None

    config_path = template_dir / "config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        cfg = {}

    return Template(
        id=template_id,
        name=cfg.get("name", template_id),
        category=cfg.get("category", ""),
        description=cfg.get("description", ""),
        path=template_dir,
    )


def list_templates() -> list[dict]:
    templates: list[dict] = []
    if not TEMPLATES_DIR.exists():
        return templates
    for folder in sorted(TEMPLATES_DIR.iterdir()):
        if not folder.is_dir():
            continue
        tpl = load_template(folder.name)
        if tpl:
            templates.append(
                {
                    "id": tpl.id,
                    "name": tpl.name,
                    "category": tpl.category,
                    "description": tpl.description,
                }
            )
    return templates


def format_size(format_id: str) -> tuple[int, int]:
    fmt = FORMATS.get(format_id, FORMATS["instagram_portrait"])
    return fmt["width"], fmt["height"]
