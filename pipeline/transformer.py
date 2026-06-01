"""
Maps a JobNimbus job record + linked contact into the permit data schema
expected by forms/fill.py.

NOTE: The 4 engineer-entered custom fields were added to JNB on 2026-05-29.
Their exact API key names are confirmed below but should be verified against
a real job once an engineer has populated them.
  - job_description   → project.job_description
  - structure         → reroof.structures  (comma-separated: "Main,Garage,...")
  - existing_panels   → solar.existing_solar_on_roof  ("Yes" / "No")
  - system_kw_ac      → solar.solar_kw_ac
"""

# Static EcoSolar contractor info — update if it ever changes
_CONTRACTOR = {
    "contractor_name": "EcoSolar USA Electric LLC",
    "contractor_phone": "7145550100",
    "contractor_license": "1045300",
    "contractor_class": ["C10", "C46"],
    "business_tax": "",
}

# Static applicant (permit coordinator)
_APPLICANT = {
    "applicant_name": "Allysa Dizon",
    "applicant_phone": "7145550123",
    "applicant_address": "",
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


def _use_type(job: dict) -> dict:
    prop_type = (job.get("Property Type") or "").lower()
    commercial = "commercial" in prop_type
    return {"residential": not commercial, "commercial": commercial}


def build_permit_data(job: dict, contact: dict) -> dict:
    owner_phone = (
        contact.get("home_phone")
        or contact.get("mobile_phone")
        or contact.get("work_phone")
        or ""
    )
    owner_name = contact.get("display_name") or (
        f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
    )

    return {
        "project": {
            "project_id": job.get("jnid", ""),
            "jurisdiction": job.get("city", ""),
            "form_type": "solar_permit_application",
            "job_description": job.get("job_description", ""),
            "valuation": "",
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
        },
        "contractor": _CONTRACTOR,
        "applicant": _APPLICANT,
        "solar": {
            "solar_panel_count": job.get("Number Panels") or job.get("cf_long_1") or "",
            "solar_kw_ac": job.get("system_kw_ac", ""),
            "existing_solar_on_roof": job.get("existing_panels", "No"),
        },
        "reroof": {
            "structures": _parse_structures(job.get("structure")),
        },
        "signature": {
            "signature": "",
            "date": "",
        },
    }
