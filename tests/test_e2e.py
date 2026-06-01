"""
End-to-end pipeline test.

Two modes:
  pytest tests/test_e2e.py                    # posts directly to webhook (fast)
  pytest tests/test_e2e.py --full-trigger     # changes job status so JNB fires webhook (full chain)

Requires env vars: JOBNIMBUS_API_KEY, WEBHOOK_URL
Cleans up the test job even if the test fails.
"""

import os
import time

import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

from pipeline import jnb_client

WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "http://localhost:8000/webhook")

# Realistic test data matching what an engineer would fill in JNB
_TEST_JOB_PAYLOAD = {
    "name": "[TEST] Garden Grove PDF Pipeline",
    "record_type": 1,
    "address_line1": "12345 Test St",
    "city": "Garden Grove",
    "state_text": "CA",
    "zip": "92840",
    # 4 engineer-entered custom fields
    "job_description": "Install roof-mounted solar PV system with 20 modules and associated electrical equipment.",
    "structure": "Main",
    "existing_panels": "No",
    "system_kw_ac": "7.2",
    # Existing named fields
    "Number Panels": 20,
}

_TEST_CONTACT_PAYLOAD = {
    "first_name": "Test",
    "last_name": "Homeowner",
    "record_type": 2,
    "address_line1": "12345 Test St",
    "city": "Garden Grove",
    "state_text": "CA",
    "zip": "92840",
    "home_phone": "7145550199",
}


@pytest.fixture
def full_trigger(request):
    return request.config.getoption("--full-trigger")


@pytest.fixture
def test_job():
    """Creates a test contact + job, yields the job record, then deletes both."""
    contact = jnb_client.create_contact(_TEST_CONTACT_PAYLOAD)
    contact_jnid = contact["jnid"]

    job_payload = {**_TEST_JOB_PAYLOAD, "primary": contact_jnid}
    job = jnb_client.create_job(job_payload)
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

    # Verify PDF was attached to the job
    files = _poll_for_attachment(jnid, timeout=30)
    assert files, "No PDF attachment found on job after pipeline ran"


def test_pipeline_via_status_trigger(test_job, full_trigger):
    """Changes job status so JNB fires the webhook — tests the full trigger chain."""
    if not full_trigger:
        pytest.skip("Pass --full-trigger to run the full JNB automation trigger test")

    # TODO: update this status name to match the JNB workflow trigger status
    TRIGGER_STATUS = os.environ.get("TRIGGER_STATUS_NAME", "Ready for Permit")

    jnid = test_job["jnid"]
    requests.put(
        f"https://app.jobnimbus.com/api1/jobs/{jnid}",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['JOBNIMBUS_API_KEY']}"},
        json={"status_name": TRIGGER_STATUS},
        timeout=15,
    ).raise_for_status()

    files = _poll_for_attachment(jnid, timeout=90)
    assert files, "No PDF attachment found — webhook may not have fired or pipeline failed"
