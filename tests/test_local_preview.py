"""
Local preview test — fetches a real JNB job, prints the transformer output,
and saves a filled PDF to output/ for visual inspection.

Usage:
    pytest tests/test_local_preview.py -s --jnid <jnid>

The -s flag keeps stdout visible so you can see the transformer output.
"""

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path.home() / ".env")

from pipeline import jnb_client
from pipeline.transformer import build_permit_data
from forms.registry import get_form
from forms.fill import fill_pdf_form


@pytest.fixture
def jnid(request):
    val = request.config.getoption("--jnid") or os.environ.get("PREVIEW_JNID")
    if not val:
        pytest.skip("Pass --jnid <jnid> to run this test")
    return val


def test_transformer_output(jnid):
    """Prints the raw JNB job + contact, then the permit data going into the PDF filler."""
    job = jnb_client.get_job(jnid)
    raw = job.get("primary") or job.get("customer")
    contact_jnid = raw.get("id") if isinstance(raw, dict) else raw
    contact = jnb_client.get_contact(contact_jnid) if contact_jnid else {}

    print("\n" + "=" * 60)
    print("RAW JNB JOB FIELDS (relevant subset)")
    print("=" * 60)
    relevant_job_keys = [
        "jnid", "name", "address_line1", "city", "state_text", "zip",
        "Property Type", "Number Panels", "System size DC",
        "job_description", "structure", "existing_panels", "system_kw_ac",
    ]
    for k in relevant_job_keys:
        if k in job:
            print(f"  {k}: {job[k]!r}")
        else:
            print(f"  {k}: (not present)")

    print("\n" + "=" * 60)
    print("RAW JNB CONTACT FIELDS (relevant subset)")
    print("=" * 60)
    relevant_contact_keys = [
        "jnid", "first_name", "last_name", "display_name",
        "email", "home_phone", "mobile_phone", "work_phone",
        "address_line1", "city", "state_text", "zip",
    ]
    for k in relevant_contact_keys:
        if k in contact:
            print(f"  {k}: {contact[k]!r}")
        else:
            print(f"  {k}: (not present)")

    permit_data = build_permit_data(job, contact)

    print("\n" + "=" * 60)
    print("PERMIT DATA → PDF FILLER INPUT")
    print("=" * 60)
    print(json.dumps(permit_data, indent=2))

    # Save permit_data to output/ for reference
    out_dir = Path(__file__).parent.parent / "output"
    out_dir.mkdir(exist_ok=True)
    data_path = out_dir / f"permit_data_{jnid}.json"
    data_path.write_text(json.dumps(permit_data, indent=2))
    print(f"\nPermit data saved to: {data_path}")


def test_pdf_output(jnid):
    """Fills the PDF and saves it to output/ for visual inspection."""
    job = jnb_client.get_job(jnid)
    raw = job.get("primary") or job.get("customer")
    contact_jnid = raw.get("id") if isinstance(raw, dict) else raw
    contact = jnb_client.get_contact(contact_jnid) if contact_jnid else {}

    permit_data = build_permit_data(job, contact)
    jurisdiction = permit_data["project"]["jurisdiction"]
    form = get_form(jurisdiction)

    out_dir = Path(__file__).parent.parent / "output"
    out_dir.mkdir(exist_ok=True)
    data_path = out_dir / f"permit_data_{jnid}.json"
    output_path = out_dir / f"preview_{jnid}.pdf"

    data_path.write_text(json.dumps(permit_data, indent=2))

    report = fill_pdf_form(
        pdf_path=form["template"],
        data_path=data_path,
        mapping_path=form["mapping"],
        output_path=output_path,
    )

    print("\n" + "=" * 60)
    print("FILL REPORT")
    print("=" * 60)
    print(json.dumps(report, indent=2))
    print(f"\nPDF saved to: {output_path}")
    print("Open it to verify the output looks correct.")

    if report["issues"]:
        print("\nWARNINGS (missing fields — expected for jobs without all custom fields filled):")
        for issue in report["issues"]:
            print(f"  - {issue['field']}: {issue['message']}")

    assert output_path.exists(), "PDF was not created"
