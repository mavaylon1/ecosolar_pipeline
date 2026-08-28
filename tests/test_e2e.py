"""
End-to-end pipeline test.

Two modes:
  pytest tests/test_e2e.py                    # posts directly to webhook (fast)
  pytest tests/test_e2e.py --full-trigger     # changes job status to Permit so JNB fires the webhook (full chain)

Requires env vars: JOBNIMBUS_API_KEY, WEBHOOK_URL
Cleans up (archives) test records even if the test fails.

Trigger: JNB automation rule → Status Changed → Permit → Webhook

Note: the pipeline re-runs (and re-attaches a PDF) every time a job's status changes
to Permit — there's no dedupe guard by design, since that lets this test run repeatedly
without needing fresh fake job/contact records each time.
"""

import os
import time

import pytest
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path.home() / ".env")

from pipeline import jnb_client

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "http://localhost:8000/webhook")

# Realistic test data matching what an engineer would fill in JNB at job creation
_TEST_JOB_PAYLOAD = {
    "name": "[TEST] Garden Grove PDF Pipeline",
    "record_type": 11,
    "address_line1": "12345 Test St",
    "city": "Garden Grove",
    "state_text": "CA",
    "zip": "92840",
    "Number Panels": 20,
    "Number of Battery": 0,
    "System size DC": 7.2,
    # 4 engineer-entered custom fields — confirmed API key names (verified 2026-07-12)
    "Job_description": "Install roof-mounted solar PV system with 20 modules and associated electrical equipment.",
    "Structure": "Main",
    "Existing_panels": "No",
    "System_kw_ac": "7.2",
}

_TEST_CONTACT_PAYLOAD = {
    "first_name": "Test",
    "last_name": "Homeowner",
    "record_type": 1,
    "address_line1": "12345 Test St",
    "city": "Garden Grove",
    "state_text": "CA",
    "zip": "92840",
    "home_phone": "7145550199",
    "email": "test.homeowner@example.com",
}


@pytest.fixture
def full_trigger(request):
    return request.config.getoption("--full-trigger")


@pytest.fixture
def test_job():
    """Creates a test contact + job with skip_automation=True so the JNB webhook
    does not fire on creation — the test controls the trigger manually via direct POST."""
    contact = jnb_client.create_contact(_TEST_CONTACT_PAYLOAD, skip_automation=True)
    contact_jnid = contact["jnid"]

    job_payload = {
        **_TEST_JOB_PAYLOAD,
        "primary": {"id": contact_jnid, "type": "contact"},
        "related": [{"id": contact_jnid, "type": "contact"}],
    }
    job = jnb_client.create_job(job_payload, skip_automation=True)
    job_jnid = job["jnid"]

    yield job

    # Cleanup runs even if test fails
    try:
        jnb_client.archive_job(job_jnid)
    except Exception:
        pass
    try:
        jnb_client.archive_contact(contact_jnid)
    except Exception:
        pass


def _poll_for_attachment(job_jnid, timeout=60, interval=3):
    """Polls JNB until a PDF attachment appears on the job or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        files = jnb_client.list_files(job_jnid)
        pdfs = [f for f in files if f.get("name", "").endswith(".pdf")]
        if pdfs:
            return pdfs
        time.sleep(interval)
    return []


def test_pipeline_via_direct_post(test_job):
    """Posts directly to the webhook — tests everything except the JNB automation trigger."""
    jnid = test_job["jnid"]

    response = requests.post(WEBHOOK_URL, json={"jnid": jnid}, timeout=60)
    assert response.status_code == 200, f"Webhook returned {response.status_code}: {response.text}"

    result = response.json()
    assert result["status"] == "ok"
    assert result["jnid"] == jnid

    files = _poll_for_attachment(jnid, timeout=30)
    assert files, "No PDF attachment found on job after pipeline ran"


def test_pipeline_via_status_trigger(full_trigger):
    """
    Creates a job (automation suppressed), then changes its status to "Permit"
    so JNB fires the webhook automatically. Tests the full trigger chain:
    JNB automation → webhook → pipeline → PDF attached.

    Requires the JNB automation rule to be configured:
      Trigger: Job → Status Changed → Permit
      Action: Webhook → WEBHOOK_URL
    """
    if not full_trigger:
        pytest.skip("Pass --full-trigger to run the full JNB automation trigger test")

    contact = jnb_client.create_contact(_TEST_CONTACT_PAYLOAD, skip_automation=True)
    contact_jnid = contact["jnid"]
    job_jnid = None

    try:
        job_payload = {
            **_TEST_JOB_PAYLOAD,
            "primary": {"id": contact_jnid, "type": "contact"},
            "related": [{"id": contact_jnid, "type": "contact"}],
        }
        job = jnb_client.create_job(job_payload, skip_automation=True)
        job_jnid = job["jnid"]

        # Status change (automation NOT suppressed here) fires the JNB automation → webhook → pipeline runs
        jnb_client.update_job(job_jnid, {"status_name": "Permit"})

        files = _poll_for_attachment(job_jnid, timeout=90)
        assert files, "No PDF attachment found — JNB automation may not be configured or pipeline failed"

    finally:
        if job_jnid:
            try:
                jnb_client.archive_job(job_jnid)
            except Exception:
                pass
        try:
            jnb_client.archive_contact(contact_jnid)
        except Exception:
            pass
