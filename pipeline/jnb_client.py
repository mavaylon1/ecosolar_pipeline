import os
import requests

_BASE = "https://app.jobnimbus.com/api1"


def _headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['JOBNIMBUS_API_KEY']}",
    }


def get_job(jnid: str) -> dict:
    r = requests.get(f"{_BASE}/jobs/{jnid}", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def get_contact(jnid: str) -> dict:
    r = requests.get(f"{_BASE}/contacts/{jnid}", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def attach_file(job_jnid: str, filename: str, data: bytes, content_type: str = "application/pdf") -> dict:
    r = requests.post(
        f"{_BASE}/files",
        headers={"Authorization": f"Bearer {os.environ['JOBNIMBUS_API_KEY']}"},
        files={"file": (filename, data, content_type)},
        data={"related_id": job_jnid, "related_type": "job"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def create_job(payload: dict) -> dict:
    r = requests.post(f"{_BASE}/jobs", headers=_headers(), json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def delete_job(jnid: str) -> None:
    r = requests.delete(f"{_BASE}/jobs/{jnid}", headers=_headers(), timeout=15)
    r.raise_for_status()


def create_contact(payload: dict) -> dict:
    r = requests.post(f"{_BASE}/contacts", headers=_headers(), json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def delete_contact(jnid: str) -> None:
    r = requests.delete(f"{_BASE}/contacts/{jnid}", headers=_headers(), timeout=15)
    r.raise_for_status()


def list_files(job_jnid: str) -> list:
    r = requests.get(
        f"{_BASE}/files",
        headers=_headers(),
        params={"filter": f'{{"must":[{{"term":{{"related.id":"{job_jnid}"}}}}]}}'},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("results", [])
