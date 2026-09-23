import csv
import io
import json
import logging
import tempfile
from pathlib import Path

from pipeline import jnb_client
from pipeline.transformer import build_permit_data
from forms.registry import find_forms, form_name
from forms.fill import fill_pdf_form
from forms.verify import build_rows

logger = logging.getLogger(__name__)


def _extract_jnid(value) -> str | None:
    """JNB returns related records as either a plain string ID or a dict with an 'id' key."""
    if isinstance(value, dict):
        return value.get("id")
    return value


def _attachment_base(jurisdiction: str, name: str | None, jnid: str) -> str:
    base = f"permit_{jurisdiction.replace(' ', '_').lower()}"
    if name:
        base += f"_{name}"
    return f"{base}_{jnid}"


def _verify_csv_bytes(data: dict, mapping_path: Path, template_path: Path) -> bytes:
    rows = build_rows(data, mapping_path, template_path)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["pdf_field", "schema_key", "jobnimbus_source", "value", "status"])
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def run_pipeline(jnid: str) -> dict:
    """Fetches the job, fills every form registered for its city, and attaches each filled
    PDF plus its VERIFY report - independently per form, so one form's issues never withhold
    another form that filled cleanly. Nothing here blocks on missing data or a bad mapping;
    those just get noted in the attached VERIFY CSV for manual review. Only a genuine
    infrastructure failure (JNB unreachable, no linked contact, a template that won't open)
    raises - see docs/GUARDRAILS.md and docs/ROADMAP.md for the reasoning."""
    logger.info("pipeline.start jnid=%s", jnid)

    job = jnb_client.get_job(jnid)
    logger.info("pipeline.job_fetched name=%r city=%r", job.get("name"), job.get("city"))

    contact_jnid = _extract_jnid(job.get("primary") or job.get("customer"))
    if not contact_jnid:
        raise ValueError(f"Job {jnid} has no linked contact")
    contact = jnb_client.get_contact(contact_jnid)

    permit_data = build_permit_data(job, contact)
    jurisdiction = permit_data["project"]["jurisdiction"]
    forms = find_forms(jurisdiction)

    if not forms:
        logger.warning("pipeline.no_forms jnid=%s city=%r", jnid, jurisdiction)
        return {"status": "no_forms", "jnid": jnid, "city": jurisdiction, "files": [], "form_reports": {}}

    attached = []
    form_reports = {}

    with tempfile.TemporaryDirectory() as tmp:
        data_path = Path(tmp) / "permit_data.json"
        data_path.write_text(json.dumps(permit_data, indent=2))

        for form in forms:
            name = form_name(form["mapping"])
            base = _attachment_base(jurisdiction, name, jnid)
            output_path = Path(tmp) / f"{base}.pdf"

            try:
                report = fill_pdf_form(
                    pdf_path=form["template"],
                    data_path=data_path,
                    mapping_path=form["mapping"],
                    output_path=output_path,
                )
            except Exception as e:
                logger.error("pipeline.form_failed jnid=%s form=%s error=%s", jnid, name or "application", e)
                form_reports[name or "application"] = {"status": "ERROR", "error": str(e)}
                continue

            form_reports[name or "application"] = report
            if report["issues"]:
                logger.info("pipeline.form_issues jnid=%s form=%s issues=%s", jnid, name or "application", report["issues"])

            pdf_bytes = output_path.read_bytes()
            csv_bytes = _verify_csv_bytes(permit_data, form["mapping"], form["template"])

            jnb_client.attach_file(jnid, f"{base}.pdf", pdf_bytes)
            jnb_client.attach_file(jnid, f"{base}_verify.csv", csv_bytes, content_type="text/csv")
            attached.extend([f"{base}.pdf", f"{base}_verify.csv"])

    logger.info("pipeline.complete jnid=%s attached=%s", jnid, attached)
    return {"status": "ok", "jnid": jnid, "city": jurisdiction, "files": attached, "form_reports": form_reports}
