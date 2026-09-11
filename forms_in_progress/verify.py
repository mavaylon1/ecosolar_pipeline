"""
Builds a per-form verification CSV: PDF field -> JobNimbus source -> actual value used,
via forms/fill.py's own field-resolution logic so the doc matches exactly what got filled.

Single shared JNB_SOURCE table and row-builder, used for every city/form - previously this
existed as two separately-maintained copies (build_verify_docs.py and
garden_grove/fill_plancheck.py) that had already drifted out of sync with each other.
"""
from pathlib import Path

import fitz

from forms.fill import _load, _build_updates, _normalize, _get_font, _text_width, best_fit_fontsize

# Human-readable JobNimbus source per schema key
JNB_SOURCE = {
    "property.job_address": "job: address_line1, city, state_text, zip",
    "property.job_address_p2": "job: address_line1, city, state_text, zip (2nd copy on page 2)",
    "property.unit": "job: address_line2",
    "project.job_description": "job: Job_description",
    "project.valuation": "calculated: round(kW)x$2,000 + batteries x$2,500",
    "project.use_type.residential": "derived: job.Property Type",
    "project.use_type.commercial": "derived: job.Property Type",
    "project.permit_types.building": "hardcoded: always false",
    "project.permit_types.electrical": "hardcoded: always true",
    "project.permit_types.mechanical": "hardcoded: always false",
    "project.permit_types.plumbing": "hardcoded: always false",
    "project.permit_types.fire": "hardcoded: always false",
    "project.permit_types.solar": "hardcoded: always true",
    "project.permit_types.demo": "hardcoded: always false",
    "owner.property_owner": "contact: first_name + last_name",
    "owner.homeowner_phone": "contact: home_phone -> mobile_phone -> work_phone",
    "owner.homeowner_email": "contact: email",
    "owner.homeowner_address": "contact: address_line1",
    "owner.homeowner_city": "contact: city",
    "owner.homeowner_state": "contact: state_text",
    "owner.homeowner_zip": "contact: zip",
    "owner.homeowner_full_address": "contact: address_line1, city, state_text, zip (combined, single-line)",
    "applicant.applicant_name": "static (EcoSolar applicant contact)",
    "applicant.applicant_name_trailing": "static (EcoSolar applicant contact, 2nd instance on form)",
    "applicant.applicant_phone": "static (EcoSolar applicant contact)",
    "applicant.applicant_email": "static (EcoSolar applicant contact)",
    "applicant.applicant_address": "static (EcoSolar applicant contact)",
    "applicant.applicant_city": "static (EcoSolar applicant contact)",
    "applicant.applicant_state": "static (EcoSolar applicant contact)",
    "applicant.applicant_zip": "static (EcoSolar applicant contact)",
    "contractor.contractor_name": "static (EcoSolar)",
    "contractor.contractor_phone": "static (EcoSolar)",
    "contractor.contractor_license": "static (EcoSolar)",
    "contractor.contractor_class": "static (EcoSolar)",
    "contractor.contractor_class_compact": "static (EcoSolar) - no-space join, for narrow license-class boxes",
    "contractor.contractor_license_class_no": "static (EcoSolar) - class + license combined",
    "contractor.business_tax": "static (EcoSolar) - NOT YET SET, needs real value",
    "contractor.contractor_address": "static (EcoSolar) - same building as applicant.applicant_address",
    "contractor.contractor_city": "static (EcoSolar) - same as applicant.applicant_city",
    "contractor.contractor_state": "static (EcoSolar) - same as applicant.applicant_state",
    "contractor.contractor_zip": "static (EcoSolar) - same as applicant.applicant_zip",
    "contractor.contractor_email": "static (EcoSolar) - same as applicant.applicant_email",
    "contractor.contractor_license_exp": "static (EcoSolar) - NOT YET SET, needs real value",
    "solar.solar_panel_count": "job: Number Panels",
    "solar.solar_kw_ac": "job: System_kw_ac -> System size DC",
    "solar.existing_solar_on_roof": "job: Existing_panels",
    "solar.battery_count": "job: Number of Battery",
    "reroof.structures.main_structure": "derived: job.Structure",
    "reroof.structures.garage": "derived: job.Structure",
    "reroof.structures.patio": "derived: job.Structure",
    "reroof.structures.accessory_structure": "derived: job.Structure",
    "signature.signature": "blank - filled at signing",
    "signature.date": "blank - filled at signing",
    "workers_comp.carrier": "static (EcoSolar) - NOT YET SET, needs real value",
    "workers_comp.policy_number": "static (EcoSolar) - NOT YET SET, needs real value",
    "workers_comp.expiration_date": "static (EcoSolar) - NOT YET SET, needs real value",
    "workers_comp.phone": "static (EcoSolar) - NOT YET SET, needs real value",
    "workers_comp.agent_name": "static (EcoSolar) - NOT YET SET, needs real value",
    "city_license.number": "static (EcoSolar, per-city) - NOT YET SET, needs real value",
    "city_license.expiration": "static (EcoSolar, per-city) - NOT YET SET, needs real value",
    "business.owner_builder_licensed_contractor": "business rule (always true - EcoSolar is the licensed contractor)",
    "business.wc_maintain_insurance": "business rule (always true - EcoSolar carries real WC insurance)",
    "business.licensed_pursuant": "business rule (always true - EcoSolar is licensed)",
    "business.disclosure_role_contractor": "business rule (always 'Contractor' - EcoSolar performs the work)",
    "business.structural_calc_required": "business rule (always 'Yes' - EcoSolar always performs structural calcs)",
    "business.filer_is_contractor": "business rule (always true - EcoSolar always files as the contractor, not the owner)",
    "business.filer_employee_of_contractor": "business rule (always true - the filer is EcoSolar's own employee/agent)",
    "solar_use.mfd": "derived: job.Property Type != Single Family/Townhome",
    "solar_use.sfd": "derived: job.Property Type == Single Family/Townhome",
    "solar_use.ess_present": "derived: job.Number of Battery > 0",
}


def build_rows(data: dict, mapping_path: Path, template_path: Path) -> list[list[str]]:
    mapping = _load(mapping_path)
    doc = fitz.open(template_path)
    widget_lookup = {w.field_name: w for page in doc for w in (page.widgets() or [])}
    available = set(widget_lookup.keys())
    doc.close()

    updates, issues = _build_updates(data, mapping, available, widget_lookup)

    rows = []
    for pdf_field, upd in sorted(updates.items()):
        schema_key = upd["schema_key"]
        source = JNB_SOURCE.get(schema_key, f"(no source note for {schema_key})")
        value = upd["value"]
        if isinstance(value, bool):
            value = "checked" if value else "unchecked"
        else:
            value = _normalize(value)
        value = str(value).replace("\n", " ")

        status = "filled"
        widget = widget_lookup.get(pdf_field)
        if widget is not None and widget.field_type_string == "Text" and value:
            fontsize = upd.get("fontsize") or best_fit_fontsize(value, widget.rect.width, _get_font(widget.text_font))
            if _text_width(value, fontsize, _get_font(widget.text_font)) > max(widget.rect.width - 4, 1):
                status = f"filled, but likely overflows box even at {fontsize}pt"

        rows.append([pdf_field, schema_key, source, value, status])

    # Look up the PDF field name(s) each missing/failed schema key was headed for, so the
    # missing rows are still identifiable by PDF field, not just internal schema key.
    field_by_schema = {}
    for schema_key, spec in mapping.get("fields", {}).items():
        if isinstance(spec, str):
            spec = {"pdf_field_name": spec}
        names = spec.get("pdf_field_names") or ([spec["pdf_field_name"]] if spec.get("pdf_field_name") else [])
        field_by_schema[schema_key] = ", ".join(names)

    for issue in issues:
        pdf_field = field_by_schema.get(issue.field, "")
        source = JNB_SOURCE.get(issue.field, f"(no source note for {issue.field})")
        rows.append([pdf_field, issue.field, source, "", f"{issue.severity}: {issue.message}"])

    return rows
