"""
Resolves a JNB job's city to every form that applies to it. No static registry - a city's
forms are whatever mapping*.json files live in forms/<normalized city name>/, discovered by
convention. Each mapping is self-describing: a "template" key names its own PDF (same folder),
so nothing external has to track which mapping goes with which template.

The only exception to plain folder-name matching is a mapping that declares its own "cities"
list - used where a job's real JNB city value doesn't match a folder name naturally derived
from the form's own name. LA County jobs come through with city="Rowland Heights" or
"Hacienda Heights" (never "LA County" - that's not a real city), so forms/la_county/'s mapping
declares "cities": ["Rowland Heights", "Hacienda Heights"]. Same idea for San Diego County,
whose jobs come through as city="San Diego".

A city with more than one form (Huntington Beach: solar + asbestos) just means more than one
mapping*.json in that folder - every one of them applies, there's no "pick one" step.
"""
from pathlib import Path

from forms.fill import _load

FORMS_DIR = Path(__file__).resolve().parent.parent.parent / "forms"


def _normalize(city: str) -> str:
    return city.strip().lower().replace(" ", "_")


def _forms_in(folder: Path) -> list[dict]:
    forms = []
    for mapping_path in sorted(folder.glob("mapping*.json")):
        mapping = _load(mapping_path)
        template_name = mapping.get("template")
        if not template_name:
            continue
        forms.append({"mapping": mapping_path, "template": folder / template_name})
    return forms


def find_forms(city: str) -> list[dict]:
    """Returns a list of {"mapping": Path, "template": Path} for every form that applies to
    `city` (a job's raw JNB city value). Empty list if nothing matches - that's the "no valid
    permit setup for this city" case, left for the caller to handle (e.g. flag for review)."""
    if not city:
        return []

    candidate = FORMS_DIR / _normalize(city)
    if candidate.is_dir():
        return _forms_in(candidate)

    # No direct folder match - fall back to scanning every mapping for a declared "cities"
    # alias list (the LA County / San Diego County case).
    city_lower = city.strip().lower()
    for folder in FORMS_DIR.iterdir():
        if not folder.is_dir():
            continue
        for mapping_path in folder.glob("mapping*.json"):
            mapping = _load(mapping_path)
            aliases = [c.strip().lower() for c in mapping.get("cities", [])]
            if city_lower in aliases:
                return _forms_in(folder)

    return []


def form_name(mapping_path: Path) -> str | None:
    """Derives an attachment-naming identifier from a mapping's filename - "mapping_solar.json"
    -> "solar". Returns None for the single-form-per-city case ("mapping.json", nothing to
    distinguish it by), so callers know to skip appending anything to the attachment name."""
    stem = mapping_path.stem
    return None if stem == "mapping" else stem.removeprefix("mapping_")
