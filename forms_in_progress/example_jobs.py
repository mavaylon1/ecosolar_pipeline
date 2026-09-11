"""
Shared helpers for pulling a real example JNB job per city, for forms_in_progress POC fills.

One function per concern, reused by every city instead of duplicating fetch/extend logic
per city:
  - find_example_job(city)   queries JNB, prefers a job with all 4 engineer-entered custom
                              fields populated, falls back to the most recent job in that
                              city if none qualify yet (the fields are new - see ROADMAP.md,
                              added 2026-05-29 - so most jobs won't have them yet). This is
                              the piece that automatically starts finding better examples as
                              more jobs get the fields filled in, with no code changes needed.
  - build_example_data(...)  wraps production build_permit_data() with the extra fields the
                              forms_in_progress mapping.json drafts need beyond the base schema
                              (contractor address, workers' comp, city license, etc.) - same
                              extension previously hardcoded per-run in build_data.py, now
                              shared across every city.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from pipeline import jnb_client
from pipeline.jnb_client import _BASE, _headers
from pipeline.runner import _extract_jnid
from pipeline.transformer import build_permit_data

CUSTOM_FIELDS = ["Job_description", "Structure", "Existing_panels", "System_kw_ac"]


def find_example_job(city: str, size: int = 50) -> dict | None:
    """Returns {"job": ..., "custom_fields_complete": bool, "missing_fields": [...]}
    for the best example job found in `city`, or None if the city has no jobs at all."""
    filt = f'{{"must":[{{"term":{{"city":"{city}"}}}}]}}'
    r = requests.get(
        f"{_BASE}/jobs",
        headers=_headers(),
        params={"filter": filt, "size": size, "sort_field": "date_created", "sort_direction": "desc"},
        timeout=15,
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None

    for job in results:
        if all(job.get(f) not in (None, "", []) for f in CUSTOM_FIELDS):
            return {"job": job, "custom_fields_complete": True, "missing_fields": []}

    newest = results[0]
    missing = [f for f in CUSTOM_FIELDS if not newest.get(f)]
    return {"job": newest, "custom_fields_complete": False, "missing_fields": missing}


def extend_permit_data(job: dict, contact: dict, base: dict) -> dict:
    """Adds the fields the forms_in_progress mapping drafts need beyond the base production
    schema. City-agnostic - same extension applies regardless of which city's job this is."""
    prop_type = (job.get("Property Type") or "").strip().lower()

    base["owner"]["homeowner_address"] = contact.get("address_line1", "")
    base["owner"]["homeowner_city"] = contact.get("city", "")
    base["owner"]["homeowner_state"] = contact.get("state_text", "")
    base["owner"]["homeowner_zip"] = contact.get("zip", "")
    # Combined single-line version, for forms with one "Address" box instead of split City/State/Zip.
    base["owner"]["homeowner_full_address"] = ", ".join(p for p in [
        contact.get("address_line1", ""), contact.get("city", ""),
        contact.get("state_text", ""), contact.get("zip", ""),
    ] if p)

    # Applicant is EcoSolar's own permit coordinator - address is static regardless of job city.
    base["applicant"]["applicant_city"] = "Garden Grove"
    base["applicant"]["applicant_state"] = "CA"
    base["applicant"]["applicant_zip"] = "92843"
    base["applicant"]["applicant_name_trailing"] = base["applicant"]["applicant_name"]

    # Contractor's business email/address are the same as the applicant's (EcoSolar's own permit
    # coordinator contact) - confirmed, not a guess. Street address is the same building, entered
    # separately here (not derived from applicant_address) since that field is one combined
    # string and these forms need street/city/state/zip split out.
    base["contractor"]["contractor_address"] = "13902 Harbor Blvd, Unit 2A"
    base["contractor"]["contractor_city"] = base["applicant"]["applicant_city"]
    base["contractor"]["contractor_state"] = base["applicant"]["applicant_state"]
    base["contractor"]["contractor_zip"] = base["applicant"]["applicant_zip"]
    base["contractor"]["contractor_email"] = base["applicant"]["applicant_email"]
    # Not currently tracked anywhere - left blank on purpose so the fill report flags it as missing.
    base["contractor"]["contractor_license_exp"] = ""

    base["workers_comp"] = {
        "carrier": "",
        "policy_number": "",
        "expiration_date": "",
        "phone": "",
        "agent_name": "",
    }

    # No-space join for narrow license-class boxes that can't fit "C10, C46" at a safe,
    # legible font size - see forms_in_progress/README.md's field-source notes.
    base["contractor"]["contractor_class_compact"] = ",".join(base["contractor"]["contractor_class"])
    base["contractor"]["contractor_license_class_no"] = (
        f"{base['contractor']['contractor_class_compact']}/{base['contractor']['contractor_license']}"
    )

    base["city_license"] = {
        "number": "",
        "expiration": "",
    }

    # Business-rule constants (not JNB-derived) - see GUARDRAILS.md
    base["business"] = {
        "owner_builder_licensed_contractor": True,
        "wc_maintain_insurance": True,
        "licensed_pursuant": True,
        "disclosure_role_contractor": True,
        # Structural calculations are always performed for EcoSolar's installs - always "Yes".
        "structural_calc_required": True,
        # Always the contractor, never the property owner - EcoSolar files every permit itself.
        "filer_is_contractor": True,
        "filer_employee_of_contractor": True,
    }

    base["solar_use"] = {
        "sfd": prop_type in ("single family", "townhome") or not prop_type,
        "mfd": prop_type not in ("single family", "townhome") and bool(prop_type) and prop_type != "commercial building",
        "ess_present": bool(job.get("Number of Battery")),
    }

    base["solar"]["battery_count"] = job.get("Number of Battery") or 0

    base["property"]["unit"] = job.get("address_line2", "")
    base["property"]["job_address_p2"] = base["property"]["job_address"]

    return base


def build_example_data(job: dict, contact: dict) -> dict:
    base = build_permit_data(job, contact)
    return extend_permit_data(job, contact, base)


def fetch_contact_for_job(job: dict) -> dict:
    contact_jnid = _extract_jnid(job.get("primary") or job.get("customer"))
    return jnb_client.get_contact(contact_jnid) if contact_jnid else {}
