"""
Local preview test — fetches a real JNB job, prints the transformer output, and saves a
filled PDF + VERIFY report per form to output/ for visual inspection.

Usage:
    pytest tests/test_local_preview.py -s --jnid <jnid>

The -s flag keeps stdout visible so you can see the transformer output.
"""

import csv
import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv(Path.home() / ".env")

from pipeline import jnb_client
from pipeline.transformer import build_permit_data
from forms.registry import find_forms, form_name
from forms.fill import fill_pdf_form
from forms.verify import build_rows


@pytest.fixture
def jnid(request):
    val = request.config.getoption("--jnid") or os.environ.get("PREVIEW_JNID")
    if not val:
        pytest.skip("Pass --jnid <jnid> to run this test")

    yield val

    # Preview artifacts are for inspecting THIS run's output, not a persistent archive —
    # remove them after the test so output/ doesn't accumulate stale files across jnids.
    out_dir = Path(__file__).parent.parent / "output"
    for path in out_dir.glob(f"*_{val}*"):
        path.unlink()


def _fetch(jnid):
    job = jnb_client.get_job(jnid)
    raw = job.get("primary") or job.get("customer")
    contact_jnid = raw.get("id") if isinstance(raw, dict) else raw
    contact = jnb_client.get_contact(contact_jnid) if contact_jnid else {}
    return job, contact


def test_transformer_output(jnid):
    """Prints the raw JNB job + contact, then the permit data going into the PDF filler."""
    job, contact = _fetch(jnid)

    print("\n" + "=" * 60)
    print("RAW JNB JOB FIELDS (relevant subset)")
    print("=" * 60)
    relevant_job_keys = [
        "jnid", "name", "address_line1", "city", "state_text", "zip",
        "Property Type", "Number Panels", "System size DC", "system_kw_ac",
        "job_description", "structure", "existing_panels",
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
    print("TRANSFORMED PERMIT DATA")
    print("=" * 60)
    print(json.dumps(permit_data, indent=2))

    out_dir = Path(__file__).parent.parent / "output"
    out_dir.mkdir(exist_ok=True)
    data_path = out_dir / f"permit_data_{jnid}.json"
    data_path.write_text(json.dumps(permit_data, indent=2))
    print(f"\nPermit data saved to: {data_path}")


def test_pdf_output(jnid):
    """Fills every form for this job's city and saves each PDF + VERIFY CSV to output/ for
    visual inspection - same forms, same reporting, that a real run would produce."""
    job, contact = _fetch(jnid)
    permit_data = build_permit_data(job, contact)
    jurisdiction = permit_data["project"]["jurisdiction"]
    forms = find_forms(jurisdiction)

    if not forms:
        pytest.skip(f"No forms registered for city {jurisdiction!r}")

    out_dir = Path(__file__).parent.parent / "output"
    out_dir.mkdir(exist_ok=True)
    data_path = out_dir / f"permit_data_{jnid}.json"
    data_path.write_text(json.dumps(permit_data, indent=2))

    for form in forms:
        name = form_name(form["mapping"]) or "application"
        output_path = out_dir / f"preview_{name}_{jnid}.pdf"

        report = fill_pdf_form(
            pdf_path=form["template"],
            data_path=data_path,
            mapping_path=form["mapping"],
            output_path=output_path,
        )

        print("\n" + "=" * 60)
        print(f"FILL REPORT — {name}")
        print("=" * 60)
        print(json.dumps(report, indent=2))
        print(f"\nPDF saved to: {output_path}")

        rows = build_rows(permit_data, form["mapping"], form["template"])
        csv_path = out_dir / f"VERIFY_{name}_{jnid}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["pdf_field", "schema_key", "jobnimbus_source", "value", "status"])
            writer.writerows(rows)
        print(f"VERIFY report saved to: {csv_path}")

        assert output_path.exists(), f"PDF was not created for {name}"
