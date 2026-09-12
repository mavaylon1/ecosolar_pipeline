import json
import logging
import tempfile
from pathlib import Path

from pipeline import jnb_client
from pipeline.transformer import build_permit_data, build_field_log, format_field_log
from forms.registry import get_form
from forms.fill import fill_pdf_form

logger = logging.getLogger(__name__)


def _extract_jnid(value) -> str | None:
    """JNB returns related records as either a plain string ID or a dict with an 'id' key."""
    if isinstance(value, dict):
        return value.get("id")
    return value


def run_pipeline(jnid: str) -> dict:
    logger.info("pipeline.start jnid=%s", jnid)

    job = jnb_client.get_job(jnid)
    logger.info("pipeline.job_fetched name=%r city=%r", job.get("name"), job.get("city"))

    contact_jnid = _extract_jnid(job.get("primary") or job.get("customer"))
    if not contact_jnid:
        raise ValueError(f"Job {jnid} has no linked contact")
    contact = jnb_client.get_contact(contact_jnid)

    permit_data = build_permit_data(job, contact)
    field_log = format_field_log(build_field_log(job, contact), job)

    logger.info("pipeline.transform_complete\n%s", field_log)

    jurisdiction = permit_data["project"]["jurisdiction"]
    form = get_form(jurisdiction)

    with tempfile.TemporaryDirectory() as tmp:
        data_path = Path(tmp) / "permit_data.json"
        output_path = Path(tmp) / "filled_permit.pdf"
        log_path = Path(tmp) / "field_log.txt"

        data_path.write_text(json.dumps(permit_data, indent=2))
        log_path.write_text(field_log)

        report = fill_pdf_form(
            pdf_path=form["template"],
            data_path=data_path,
            mapping_path=form["mapping"],
            output_path=output_path,
        )

        if report["status"] != "passed":
            logger.error("pipeline.fill_failed jnid=%s issues=%s", jnid, report["issues"])
            raise RuntimeError(f"PDF fill issues: {report['issues']}")

        pdf_bytes = output_path.read_bytes()
        log_bytes = log_path.read_bytes()

    base = f"permit_{jurisdiction.replace(' ', '_').lower()}_{jnid}"
    jnb_client.attach_file(jnid, f"{base}.pdf", pdf_bytes)
    jnb_client.attach_file(jnid, f"{base}_field_log.txt", log_bytes, content_type="text/plain")

    logger.info("pipeline.complete jnid=%s", jnid)
    return {"status": "ok", "jnid": jnid, "files": [f"{base}.pdf", f"{base}_field_log.txt"], "fill_report": report}
