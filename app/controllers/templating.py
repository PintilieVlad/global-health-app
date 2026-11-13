"""The Jinja2 templates of the presentation layer (autoescaping is on for .html files)."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")
