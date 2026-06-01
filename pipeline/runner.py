import json
import tempfile
from pathlib import Path

from pipeline import jnb_client
from pipeline.transformer import build_permit_data
from forms.registry import get_form
from forms.fill import fill_pdf_form


def run_pipeline(jnid: str) -> dict:
    job = jnb_client.get_job(jnid)

    contact_jnid = job.get("primary") or job.get("customer")
    if not contact_jnid:
        raise ValueError(f"Job {jnid} has no linked contact")
    contact = jnb_client.get_contact(contact_jnid)

    permit_data = build_permit_data(job, contact)

    jurisdiction = permit_data["project"]["jurisdiction"]
    form = get_form(jurisdiction)

    with tempfile.TemporaryDirectory() as tmp:
        data_path = Path(tmp) / "permit_data.json"
        output_path = Path(tmp) / "filled_permit.pdf"

        data_path.write_text(json.dumps(permit_data, indent=2))

        report = fill_pdf_form(
            pdf_path=form["template"],
            data_path=data_path,
            mapping_path=form["mapping"],
            output_path=output_path,
        )

        if report["status"] != "passed":
            raise RuntimeError(f"PDF fill issues: {report['issues']}")

        pdf_bytes = output_path.read_bytes()

    filename = f"permit_{jurisdiction.replace(' ', '_').lower()}_{jnid}.pdf"
    jnb_client.attach_file(jnid, filename, pdf_bytes)

    return {"status": "ok", "jnid": jnid, "file": filename, "fill_report": report}
