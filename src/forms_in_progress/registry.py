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

# This file lives at src/forms_in_progress/registry.py, but the actual template PDFs/mappings
# are data, not code - they stay at the repo-root forms_in_progress/ directory instead of
# moving under src/.
ROOT = Path(__file__).resolve().parent.parent.parent
HERE = ROOT / "forms_in_progress"

# Every template PDF below lives inside forms_in_progress/<city>/, next to its mapping - once a
# form has a tested mapping, its template belongs here, not in pending_forms/pending_forms_fillable
# (those hold forms that don't have a mapping yet). Garden Grove's "plancheck" entry is the one
# exception - it deliberately points at the live production template in forms/.

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
                "template": HERE / "garden_grove/permit-declaration-3-25-20.pdf",
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
                "template": HERE / "fountain_valley/Permit Application page 1_201504201306210151.pdf",
                "mapping": HERE / "fountain_valley/mapping.json",
            },
        },
    },
    "huntington_beach": {
        "display_name": "Huntington Beach",
        "pinned_jnid": None,
        "forms": {
            "solar": {
                "template": HERE / "huntington_beach/Photovoltaic Solar Permit (Residential Only) Application.pdf",
                "mapping": HERE / "huntington_beach/mapping_solar.json",
            },
            "asbestos": {
                "template": HERE / "huntington_beach/Permit & Asbestos Disclosure Form.pdf",
                "mapping": HERE / "huntington_beach/mapping_asbestos.json",
            },
        },
    },
    "westminster": {
        "display_name": "Westminster",
        "pinned_jnid": None,
        "forms": {
            # Template is the FIXED copy (built by westminster/fix_address_field.py from the raw
            # "Building Permit Application.pdf" also in this folder) - the original city PDF
            # reused the same "Address" field name for Owner/Applicant/Contractor address boxes.
            # That's a genuine one-off edge case, not something the generic pipeline handles.
            "application": {
                "template": HERE / "westminster/Building Permit Application_fixed.pdf",
                "mapping": HERE / "westminster/mapping_application.json",
            },
            "declaration": {
                "template": HERE / "westminster/Building Permit Declaration.pdf",
                "mapping": HERE / "westminster/mapping_declaration.json",
            },
        },
    },
    "anaheim": {
        "display_name": "Anaheim",
        "pinned_jnid": None,
        "forms": {
            # B701 (Permit Extension Request) can't be mapped from JNB data at all - see
            # not_possible_forms/README.md for why.
            "b715": {
                "template": HERE / "anaheim/B715_fillable.pdf",
                "mapping": HERE / "anaheim/mapping_b715.json",
            },
            "b705": {
                "template": HERE / "anaheim/B705_fillable.pdf",
                "mapping": HERE / "anaheim/mapping_b705.json",
            },
        },
    },
    "corona": {
        "display_name": "Corona",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": HERE / "corona/Corona_fillable.pdf",
                "mapping": HERE / "corona/mapping.json",
            },
        },
    },
    "pomona": {
        "display_name": "Pomona",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": HERE / "pomona/Pomona_fillable.pdf",
                "mapping": HERE / "pomona/mapping.json",
            },
        },
    },
    "stanton": {
        "display_name": "Stanton",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": HERE / "stanton/PermitApplication_fillable.pdf",
                "mapping": HERE / "stanton/mapping.json",
            },
        },
    },
    "yorba_linda": {
        "display_name": "Yorba Linda",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": HERE / "yorba_linda/BuildingSubmittalForm_fillable.pdf",
                "mapping": HERE / "yorba_linda/mapping.json",
            },
        },
    },
    "redlands": {
        "display_name": "Redlands",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": HERE / "redlands/BuildingPermitApplication_fillable.pdf",
                "mapping": HERE / "redlands/mapping.json",
            },
        },
    },
    "san_diego_county": {
        "display_name": "San Diego County",
        # "San Diego County" isn't a real JNB city value - jobs in San Diego are entered under
        # "San Diego" itself, same class of city-vs-county naming gap as LA County, but here the
        # incorporated city's own name happens to be the right substitute (confirmed via real
        # data during Phase A), not a different unincorporated-community name.
        "jnb_city": "San Diego",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": HERE / "san_diego_county/pds291_fillable.pdf",
                "mapping": HERE / "san_diego_county/mapping.json",
            },
        },
    },
    "long_beach": {
        "display_name": "Long Beach",
        "pinned_jnid": None,
        "forms": {
            # app-011 ("Express Building Permit Application") isn't mapped here - its scope is a
            # repair/remodel questionnaire with no solar content, and it's unclear it's even the
            # right document for solar permits. See ask_ecosolar/README.md.
            "electrical": {
                "template": HERE / "long_beach/app-012_fillable.pdf",
                "mapping": HERE / "long_beach/mapping_012.json",
            },
        },
    },
    "irvine": {
        "display_name": "Irvine",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": HERE / "irvine/MinorResidentialOTC_fillable.pdf",
                "mapping": HERE / "irvine/mapping.json",
            },
        },
    },
    "fullerton": {
        "display_name": "Fullerton",
        "pinned_jnid": None,
        "forms": {
            "application": {
                "template": HERE / "fullerton/SolarPermitApplication_fillable.pdf",
                "mapping": HERE / "fullerton/mapping.json",
            },
        },
    },
    "la_county": {
        "display_name": "Los Angeles County",
        # "Los Angeles County" isn't a real JNB city value - it's not a city at all, and matching
        # the incorporated City of Los Angeles isn't right either (it has its own building dept,
        # LADBS, separate from the county). The correct test is "is this address unincorporated
        # LA County territory," which JNB doesn't track directly - this list of known
        # unincorporated LA County communities (tried in order until one has a job) is a stopgap
        # until there's a real city/address -> county mapper. See ROADMAP.md Phase 3.
        "jnb_city": ["Rowland Heights", "Hacienda Heights"],
        "pinned_jnid": None,
        "forms": {
            "declaration": {
                "template": HERE / "la_county/LACountyBSDPermitDeclaration_fillable.pdf",
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
