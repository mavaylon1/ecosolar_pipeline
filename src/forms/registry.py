from pathlib import Path

# This file lives at src/forms/registry.py, but the actual template PDFs/mappings are data,
# not code - they stay at the repo-root forms/ directory instead of moving under src/.
_FORMS_DIR = Path(__file__).resolve().parent.parent.parent / "forms"

REGISTRY = {
    "garden grove": {
        "mapping": _FORMS_DIR / "garden_grove" / "mapping.json",
        "template": _FORMS_DIR / "garden_grove" / "template.pdf",
    },
}


def get_form(jurisdiction: str) -> dict:
    key = jurisdiction.lower().strip()
    if key not in REGISTRY:
        raise ValueError(f"No PDF form registered for jurisdiction: {jurisdiction!r}")
    return REGISTRY[key]
