from pathlib import Path

_FORMS_DIR = Path(__file__).parent

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
