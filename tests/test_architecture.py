"""Task 3.4: the dependency rule, checked automatically.

The lower layers must not depend on the web layer above them: app/domain.py and the
files in app/repositories/ and app/services/ may not import FastAPI, the controllers
or the dependency wiring.
"""

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP = PROJECT_ROOT / "app"
FORBIDDEN = ("fastapi", "app.controllers", "app.dependencies")


def imported_modules(path: Path) -> set[str]:
    """Names of the modules imported by one Python file."""
    modules = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _is_forbidden(module: str) -> bool:
    """True for a forbidden module or any module inside it (e.g. fastapi.responses)."""
    return any(module == name or module.startswith(f"{name}.") for name in FORBIDDEN)


LOWER_LAYER_FILES = [
    APP / "domain.py",
    *sorted((APP / "repositories").glob("*.py")),
    *sorted((APP / "services").glob("*.py")),
]


@pytest.mark.parametrize(
    "path", LOWER_LAYER_FILES, ids=lambda path: str(path.relative_to(PROJECT_ROOT))
)
def test_lower_layers_do_not_import_the_web_layer(path: Path) -> None:
    forbidden = sorted(module for module in imported_modules(path) if _is_forbidden(module))

    assert not forbidden, f"{path.relative_to(PROJECT_ROOT)} imports {forbidden}"
