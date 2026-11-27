"""Todo import de `app/` debe estar en requirements.txt (producción), no solo en el de desarrollo."""

import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
# El nombre del paquete en pip no siempre coincide con el del módulo.
PIP_NAME = {
    "jwt": "pyjwt",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "google": "google-genai",
    "multipart": "python-multipart",
    "pydantic_settings": "pydantic-settings",
}
# Llegan solas como dependencias de fastapi / uvicorn.
TRANSITIVE = {"starlette", "anyio"}


def _third_party_imports() -> set[str]:
    found: set[str] = set()
    for path in (BACKEND / "app").rglob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*(?:import|from)\s+([A-Za-z_]\w*)", line)
            if match:
                found.add(match.group(1))
    return {m for m in found if m not in sys.stdlib_module_names and m != "app"}


def test_production_requirements_cover_every_import():
    declared = (BACKEND / "requirements.txt").read_text(encoding="utf-8").lower()
    missing = sorted(
        module
        for module in _third_party_imports() - TRANSITIVE
        if PIP_NAME.get(module, module).lower().replace("_", "-") not in declared
    )

    assert missing == [], f"Faltan en requirements.txt: {missing}"
