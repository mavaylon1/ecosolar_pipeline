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

import math

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
    kw_raw = job.get("system_kw_ac") or job.get("System size DC")
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


def build_field_log(job: dict, contact: dict) -> list[dict]:
    """
    Returns a list of entries showing exactly which JNB field fed each PDF field,
    what value was used, and whether it was found, a fallback, or missing.
    """
    entries = []

    def row(pdf_field, jnb_source, value, note=None):
        if value is None or value == "" or value == []:
            status = "MISSING"
            display = "(missing)"
        else:
            status = note if note else "found"
            display = str(value)
        entries.append({
            "pdf_field": pdf_field,
            "jnb_source": jnb_source,
            "value": display,
            "status": status,
        })

    # Property address
    row("Job Address",
        "job: address_line1, city, state_text, zip",
        _job_address(job))

    # Homeowner
    owner_name = (
        f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        or contact.get("display_name", "")
    )
    row("Property Owner", "contact: first_name + last_name", owner_name)

    phone_src = ("home_phone" if contact.get("home_phone")
                 else "mobile_phone" if contact.get("mobile_phone")
                 else "work_phone")
    owner_phone = contact.get("home_phone") or contact.get("mobile_phone") or contact.get("work_phone")
    row("HO Phone (Phone No / undefined)", f"contact: {phone_src}", owner_phone)

    row("HO Email", "contact: email", contact.get("email"))

    # Property type
    prop_type = job.get("Property Type", "")
    use = _use_type(job)
    row("Residential / Commercial (checkboxes)",
        "job: Property Type",
        prop_type,
        note=f"→ residential={use['residential']}, commercial={use['commercial']}")

    # Permit types
    row("Electrical (checkbox)", "[hardcoded: always true]", "✓", note="hardcoded")
    row("Solar (checkbox)",      "[hardcoded: always true]", "✓", note="hardcoded")

    # Contractor (static)
    row("Contractor",                     "[static]", _CONTRACTOR["contractor_name"], note="static")
    row("Contractor Phone (No_2 / undef_2)", "[static]", _CONTRACTOR["contractor_phone"], note="static")
    row("State License",                  "[static]", _CONTRACTOR["contractor_license"], note="static")
    row("Class",                          "[static]", ", ".join(_CONTRACTOR["contractor_class"]), note="static")

    # Applicant (static)
    row("Applicant",                      "[static]", _APPLICANT["applicant_name"], note="static")
    row("Applicant Phone (No_3 / undef_3)", "[static]", _APPLICANT["applicant_phone"], note="static")
    row("Applicant Address",              "[static]", _APPLICANT["applicant_address"], note="static")
    row("Applicant Email",                "[static]", _APPLICANT["applicant_email"], note="static")

    # Valuation (calculated)
    batteries = job.get("Number of Battery") or 0
    row("Valuation",
        "calculated: round(kW)×$2000 + batteries×$2500",
        _calc_valuation(job),
        note=f"kW={job.get('system_kw_ac') or job.get('System size DC') or '?'}, batteries={batteries}")

    # Job description (engineer-entered)
    row("Job Description 1/2/3", "job: job_description", job.get("job_description"))

    # Panel count
    row("Panel Count (undefined_4)", "job: Number Panels", job.get("Number Panels"))

    # kW — AC preferred, DC fallback
    kw_ac = job.get("system_kw_ac")
    kw_dc = job.get("System size DC")
    if kw_ac:
        row("System kW (undefined_5)", "job: system_kw_ac", kw_ac)
    elif kw_dc:
        row("System kW (undefined_5)", "job: System size DC", kw_dc, note="fallback — system_kw_ac missing")
    else:
        row("System kW (undefined_5)", "job: system_kw_ac / System size DC", None)

    # Existing panels (engineer-entered)
    row("Existing Solar (radio)", "job: existing_panels", job.get("existing_panels"))

    # Structure checkboxes (engineer-entered)
    row("Structure checkboxes (Main/Garage/Patio/Accessory)",
        "job: structure", job.get("structure"))

    return entries


def format_field_log(entries: list[dict], job: dict) -> str:
    lines = [
        f"FIELD MAPPING LOG — {job.get('name', '')} | {job.get('jnid', '')}",
        "",
        f"{'PDF FIELD':<48} {'JNB SOURCE':<42} {'VALUE':<30} STATUS",
        "─" * 130,
    ]
    for e in entries:
        lines.append(
            f"{e['pdf_field']:<48} {e['jnb_source']:<42} {e['value']:<30} {e['status']}"
        )
    missing = [e for e in entries if e["status"] == "MISSING"]
    lines += [
        "",
        f"Total fields: {len(entries)}  |  Missing: {len(missing)}",
    ]
    if missing:
        lines.append("Missing: " + ", ".join(e["pdf_field"] for e in missing))
    return "\n".join(lines)


def build_permit_data(job: dict, contact: dict) -> dict:
    owner_name = (
        f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        or contact.get("display_name", "")
    )
    owner_phone = (
        contact.get("home_phone")
        or contact.get("mobile_phone")
        or contact.get("work_phone")
        or ""
    )
    owner_email = contact.get("email", "")

    return {
        "project": {
            "project_id": job.get("jnid", ""),
            "jurisdiction": job.get("city", ""),
            "form_type": "solar_permit_application",
            "job_description": job.get("job_description", ""),
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
                job.get("system_kw_ac")
                or job.get("System size DC")
                or ""
            ),
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
