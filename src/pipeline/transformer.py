"""
Maps a JobNimbus job record + linked contact into the permit data schema
expected by forms/fill.py.

NOTE: The 4 engineer-entered custom fields were added to JNB on 2026-05-29.
Confirmed API key names (verified 2026-07-12):
  - Job_description   → project.job_description
  - Structure         → reroof.structures  (comma-separated: "Main,Garage,...")
  - Existing_panels   → solar.existing_solar_on_roof  ("Yes" / "No")
  - System_kw_ac      → solar.solar_kw_ac
"""

# Static EcoSolar contractor info — update if it ever changes
_CONTRACTOR = {
    "contractor_name": "Ecosolar USA Electric LLC",
    "contractor_phone": "7142659077",
    "contractor_license": "1045300",
    "contractor_class": ["C10", "C46"],
    "business_tax": "",
}

# Static applicant (permit coordinator)
_APPLICANT = {
    "applicant_name": "Allysa Dizon",
    "applicant_phone": "6576295991",
    "applicant_address": "13902 Harbor Blvd, Unit 2A, Garden Grove CA 92843",
    "applicant_email": "permit@ecosolarusa.com",
}

_STRUCTURE_MAP = {
    "main":                "main_structure",
    "main structure":      "main_structure",
    "garage":              "garage",
    "patio":               "patio",
    "accessory":           "accessory_structure",
    "accessory structure": "accessory_structure",
}


def _parse_structures(value: str | None) -> dict:
    base = {"main_structure": False, "garage": False, "patio": False, "accessory_structure": False}
    if not value:
        return base
    for part in value.split(","):
        key = _STRUCTURE_MAP.get(part.strip().lower())
        if key:
            base[key] = True
    return base


def _job_address(job: dict) -> str:
    parts = [
        job.get("address_line1", ""),
        job.get("city", ""),
        job.get("state_text", ""),
        job.get("zip", ""),
    ]
    return ", ".join(p for p in parts if p)


def _calc_valuation(job: dict) -> str:
    kw_raw = job.get("System_kw_ac") or job.get("System size DC")
    if not kw_raw:
        return ""
    batteries = int(job.get("Number of Battery") or 0)
    try:
        kw = float(kw_raw)
    except (ValueError, TypeError):
        return ""
    total = round(kw) * 2000 + batteries * 2500
    return str(total)


_COMMERCIAL_TYPES = {"commercial building"}

def _use_type(job: dict) -> dict:
    prop_type = (job.get("Property Type") or "").strip().lower()
    commercial = prop_type in _COMMERCIAL_TYPES
    return {"residential": not commercial, "commercial": commercial}


def _owner_name(contact: dict) -> str:
    return (
        f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        or contact.get("display_name", "")
    )


def _owner_phone(contact: dict) -> tuple[str, str]:
    """Returns (phone value, which contact field it came from) - home preferred, then
    mobile, then work."""
    for field in ("home_phone", "mobile_phone", "work_phone"):
        if contact.get(field):
            return contact[field], field
    return "", "work_phone"


def build_permit_data(job: dict, contact: dict) -> dict:
    owner_name = _owner_name(contact)
    owner_phone, _ = _owner_phone(contact)
    owner_email = contact.get("email", "")

    return {
        "project": {
            "project_id": job.get("jnid", ""),
            "jurisdiction": job.get("city", ""),
            "form_type": "solar_permit_application",
            "job_description": job.get("Job_description", ""),
            "valuation": _calc_valuation(job),
            "use_type": _use_type(job),
            "permit_types": {
                "building": False,
                "electrical": True,
                "mechanical": False,
                "plumbing": False,
                "fire": False,
                "solar": True,
                "demo": False,
            },
        },
        "property": {
            "job_address": _job_address(job),
        },
        "owner": {
            "property_owner": owner_name,
            "homeowner_phone": owner_phone,
            "homeowner_email": owner_email,
        },
        "contractor": _CONTRACTOR,
        "applicant": _APPLICANT,
        "solar": {
            "solar_panel_count": job.get("Number Panels") or "",
            "solar_kw_ac": (
                job.get("System_kw_ac")
                or job.get("System size DC")
                or ""
            ),
            "existing_solar_on_roof": job.get("Existing_panels", "No"),
        },
        "reroof": {
            "structures": _parse_structures(job.get("Structure")),
        },
        "signature": {
            "signature": "",
            "date": "",
        },
    }
