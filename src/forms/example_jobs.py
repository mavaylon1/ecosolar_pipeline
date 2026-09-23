"""
Shared helpers for pulling a real example JNB job per city, used by build_data.py/run_all.py
to test-fill every form in forms/ against real data without touching a real job.

One function per concern, reused by every city instead of duplicating fetch/extend logic
per city:
  - find_example_job(city)   queries JNB, prefers a job with all 4 engineer-entered custom
                              fields populated, falls back to the most recent job in that
                              city if none qualify yet (the fields are new - see ROADMAP.md,
                              added 2026-05-29 - so most jobs won't have them yet). This is
                              the piece that automatically starts finding better examples as
                              more jobs get the fields filled in, with no code changes needed.
  - build_example_data(...)  wraps production build_permit_data() with the extra fields some
                              forms' mapping.json need beyond the base schema (contractor
                              address, workers' comp, city license, etc.) - same extension
                              previously hardcoded per-run in build_data.py, now shared
                              across every city.
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


def _contact_has_address(job: dict) -> bool:
    """Fetches the job's linked contact and checks whether it has a real street address.
    Some jobs have their 'primary' contact wired to a business/referral entity instead of
    the actual homeowner - e.g. Westminster's "HOANG VU*DV*ADU" job links to contact
    "DV Construction" (a subcontractor, per its own name), not homeowner Hoang Vu, so
    homeowner_address ends up blank on the filled form even though nothing about the
    mapping or the job's own fields looks wrong. Used to skip past those when picking an
    example - job-level richness alone doesn't catch this, since the job record itself can
    be fully populated while the contact it points to is the wrong one."""
    contact_jnid = _extract_jnid(job.get("primary") or job.get("customer"))
    if not contact_jnid:
        return False
    contact = jnb_client.get_contact(contact_jnid)
    return bool(contact.get("address_line1"))


def find_example_job(city: str, size: int = 50) -> dict | None:
    """Returns {"job": ..., "custom_fields_complete": bool, "missing_fields": [...]}
    for the best example job found in `city`, or None if the city has no jobs at all.

    Ranks candidates in this order: newest job with all 4 custom fields AND a real
    contact address, then newest with all 4 custom fields regardless of contact, then
    richest job (most populated fields overall) with a real contact address, then just the
    richest job. The old all-or-nothing fallback - when no job in the city has all 4 custom
    fields - handed back the literal newest job regardless of what it was, which in practice
    was often a thin post-install service ticket ("Solar Production Issue for...", "Permit
    Information Request for...") rather than a real install job; richness fixed that. This
    adds the contact-address check on top, since richness alone doesn't catch a job whose
    own fields are fine but whose linked contact is a business entity with no address."""
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

    complete = [j for j in results if all(j.get(f) not in (None, "", []) for f in CUSTOM_FIELDS)]
    for job in complete:
        if _contact_has_address(job):
            return {"job": job, "custom_fields_complete": True, "missing_fields": []}
    if complete:
        return {"job": complete[0], "custom_fields_complete": True, "missing_fields": []}

    def richness(job):
        return sum(1 for v in job.values() if v not in (None, "", [], {}))

    by_richness = sorted(results, key=richness, reverse=True)
    for job in by_richness:
        if _contact_has_address(job):
            missing = [f for f in CUSTOM_FIELDS if not job.get(f)]
            return {"job": job, "custom_fields_complete": False, "missing_fields": missing}

    newest = by_richness[0]
    missing = [f for f in CUSTOM_FIELDS if not newest.get(f)]
    return {"job": newest, "custom_fields_complete": False, "missing_fields": missing}


def extend_permit_data(job: dict, contact: dict, base: dict) -> dict:
    """Adds fields some mappings need beyond the base production schema. City-agnostic - same
    extension applies regardless of which city's job this is."""
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
    # City+state+zip only (no street) - for forms with a separate "Address" box plus a
    # separate "City/State/Zip" box, so street doesn't get duplicated across both.
    base["owner"]["homeowner_city_zip"] = ", ".join(p for p in [
        contact.get("city", ""),
        " ".join(p2 for p2 in [contact.get("state_text", ""), contact.get("zip", "")] if p2),
    ] if p)

    # Applicant is EcoSolar's own permit coordinator - address is static regardless of job city.
    base["applicant"]["applicant_city"] = "Garden Grove"
    base["applicant"]["applicant_state"] = "CA"
    base["applicant"]["applicant_zip"] = "92843"
    base["applicant"]["applicant_name_trailing"] = base["applicant"]["applicant_name"]
    # Street only (no city/state/zip) and city/state/zip only (no street) - same split-box need
    # as owner_city_zip above. Same building as contractor_address, set below.
    base["applicant"]["applicant_street"] = "13902 Harbor Blvd, Unit 2A"
    base["applicant"]["applicant_city_zip"] = f"{base['applicant']['applicant_city']}, {base['applicant']['applicant_state']} {base['applicant']['applicant_zip']}"

    # Contractor's business email/address are the same as the applicant's (EcoSolar's own permit
    # coordinator contact) - confirmed, not a guess. Street address is the same building, entered
    # separately here (not derived from applicant_address) since that field is one combined
    # string and these forms need street/city/state/zip split out.
    base["contractor"]["contractor_address"] = "13902 Harbor Blvd, Unit 2A"
    base["contractor"]["contractor_city"] = base["applicant"]["applicant_city"]
    base["contractor"]["contractor_state"] = base["applicant"]["applicant_state"]
    base["contractor"]["contractor_zip"] = base["applicant"]["applicant_zip"]
    base["contractor"]["contractor_email"] = base["applicant"]["applicant_email"]
    base["contractor"]["contractor_city_zip"] = base["applicant"]["applicant_city_zip"]
    base["contractor"]["contractor_phone_email"] = f"{base['contractor']['contractor_phone']} / {base['contractor']['contractor_email']}"
    base["contractor"]["contractor_full_address"] = f"{base['contractor']['contractor_address']}, {base['contractor']['contractor_city_zip']}"
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
    # legible font size - see docs/PENDING_FORMS_CONVERSION_NOTES.md's field-source notes.
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
        # For forms with only a coarse Building-vs-Grading permit-type split (no separate
        # Electrical/Solar category, unlike Garden Grove's) - solar/electrical work always
        # falls under "Building," never "Grading." Distinct from project.permit_types.building,
        # which has an established narrower meaning on multi-category forms and stays False there.
        "requires_building_permit": True,
    }

    base["solar_use"] = {
        "sfd": prop_type in ("single family", "townhome") or not prop_type,
        "mfd": prop_type not in ("single family", "townhome") and bool(prop_type) and prop_type != "commercial building",
        "ess_present": bool(job.get("Number of Battery")),
    }

    base["solar"]["battery_count"] = job.get("Number of Battery") or 0
    # Pure DC value, no AC-preferred fallback - for forms that ask for DC and AC as two
    # separate distinct fields (solar_kw_ac already has its own AC-preferred/DC-fallback
    # logic from the base schema, which stays correct for forms with only one kW field).
    base["solar"]["solar_kw_dc"] = job.get("System size DC") or ""
    # Pure AC value, no DC fallback - for the same dual-field forms as solar_kw_dc above.
    # solar_kw_ac's DC fallback is correct when a form has only one kW field (better to show
    # a best-available number than nothing), but it's wrong for a form that displays DC and
    # AC as two separate line items: when AC is genuinely unknown, the fallback makes AC
    # silently duplicate the DC value instead of just being blank (caught on Corona's kW
    # AC/DC pair during Phase A review - see pending_forms_fillable/STATUS.md history).
    base["solar"]["solar_kw_ac_only"] = job.get("System_kw_ac") or ""

    base["property"]["job_address_p2"] = base["property"]["job_address"]
    base["property"]["job_city"] = job.get("city", "")
    # No property.unit field - JNB's address_line2 isn't reliably a suite/unit number (one job
    # had "New owner: Nga Nguyen" typed into it instead), and job_address never included it
    # anyway. Decided 2026-09-20: don't surface it on any form, not even folded into the main
    # address - a garbage value there would contaminate the primary address line.

    return base


def build_example_data(job: dict, contact: dict) -> dict:
    base = build_permit_data(job, contact)
    return extend_permit_data(job, contact, base)


def fetch_contact_for_job(job: dict) -> dict:
    contact_jnid = _extract_jnid(job.get("primary") or job.get("customer"))
    return jnb_client.get_contact(contact_jnid) if contact_jnid else {}
