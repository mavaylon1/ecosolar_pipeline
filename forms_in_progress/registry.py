"""
Single source of truth for every (city, form) pair being tested in forms_in_progress.

Everything else - build_data.py (pulls example jobs), run_all.py (fills + writes verify
docs) - reads from FORMS below. To add a new city or an additional form for an existing
city, add one entry here; no other file needs to change.

A city can have more than one form (Huntington Beach: solar + asbestos; Westminster:
application + declaration) - all forms for a city share that one city's permit_data.json,
since the extended schema (see example_jobs.py) is a superset every mapping.json can pull
from regardless of which fields a given form actually uses.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
HERE = Path(__file__).parent
PENDING = ROOT / "pending_forms"
PENDING_FILLABLE = ROOT / "pending_forms_fillable"

FORMS = {
    "garden_grove": {
        "display_name": "Garden Grove",
        # Pinned to a known-good example (Emmanuel Cruz ADU) instead of querying for the
        # newest job, same as every other city - kept deliberately stable across reruns
        # since this is the most heavily reviewed example. Still re-fetched live each run
        # (not a frozen file) so it reflects any updates made to that job in JobNimbus.
        "pinned_jnid": "132f8a31349541118fa4fb380e9ac75c",
        "forms": {
            "declaration": {
                "template": PENDING / "garden_grove/permit-declaration-3-25-20.pdf",
                "mapping": HERE / "garden_grove/mapping_declaration.json",
            },
            # Fills the ACTUAL production Garden Grove template/mapping (forms/garden_grove/)
            # using this same example job, as a live sanity check of the production form -
            # not a separate draft form.
            "plancheck": {
                "template": ROOT / "forms/garden_grove/template.pdf",
                "mapping": ROOT / "forms/garden_grove/mapping.json",
            },
        },
    },
    "fountain_valley": {
        "display_name": "Fountain Valley",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": PENDING / "fountain_valley/Permit Application page 1_201504201306210151.pdf",
                "mapping": HERE / "fountain_valley/mapping.json",
            },
        },
    },
    "huntington_beach": {
        "display_name": "Huntington Beach",
        "pinned_jnid": None,
        "forms": {
            "solar": {
                "template": PENDING / "huntington_beach/Photovoltaic Solar Permit (Residential Only) Application.pdf",
                "mapping": HERE / "huntington_beach/mapping_solar.json",
            },
            "asbestos": {
                "template": PENDING / "huntington_beach/Permit & Asbestos Disclosure Form.pdf",
                "mapping": HERE / "huntington_beach/mapping_asbestos.json",
            },
        },
    },
    "westminster": {
        "display_name": "Westminster",
        "pinned_jnid": None,
        "forms": {
            # Template is the FIXED copy (built by westminster/fix_address_field.py) - the
            # original city PDF reused the same "Address" field name for Owner/Applicant/
            # Contractor address boxes. That's a genuine one-off edge case, not something
            # the generic pipeline handles - see fix_address_field.py.
            "application": {
                "template": HERE / "westminster/Building Permit Application_fixed.pdf",
                "mapping": HERE / "westminster/mapping_application.json",
            },
            "declaration": {
                "template": PENDING / "westminster/Building Permit Declaration.pdf",
                "mapping": HERE / "westminster/mapping_declaration.json",
            },
        },
    },
    "anaheim": {
        "display_name": "Anaheim",
        "pinned_jnid": None,
        "forms": {
            # B701 (Permit Extension Request) intentionally not registered here - see
            # pending_forms/anaheim/ and pending_forms_fillable/STATUS.md for why.
            "b715": {
                "template": PENDING_FILLABLE / "anaheim/B715_fillable.pdf",
                "mapping": HERE / "anaheim/mapping_b715.json",
            },
        },
    },
    "fullerton": {
        "display_name": "Fullerton",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": PENDING_FILLABLE / "fullerton/SolarPermitApplication_fillable.pdf",
                "mapping": HERE / "fullerton/mapping.json",
            },
        },
    },
    "la_county": {
        "display_name": "Los Angeles County",
        "pinned_jnid": None,
        "forms": {
            "declaration": {
                "template": PENDING_FILLABLE / "la_county/LACountyBSDPermitDeclaration_fillable.pdf",
                "mapping": HERE / "la_county/mapping.json",
            },
        },
    },
}


def city_dir(city_key: str) -> Path:
    d = HERE / city_key
    d.mkdir(exist_ok=True)
    return d


def data_path(city_key: str) -> Path:
    """Garden Grove keeps its data file at the top level (long-standing existing path,
    predates this registry); every other city gets one under its own subfolder."""
    if city_key == "garden_grove":
        return HERE / "permit_data.json"
    return city_dir(city_key) / "permit_data.json"


def output_dir() -> Path:
    """All generated artifacts (filled PDFs, verify CSVs, fill_reports.json) live here -
    nothing else depends on files in this directory being current, so it's always safe to
    delete and regenerate via run_all.py."""
    d = HERE / "output"
    d.mkdir(exist_ok=True)
    return d
