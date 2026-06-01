# EcoSolar Permit Pipeline

Automated pipeline that fills city permit application PDFs using job data from JobNimbus. An engineer fills a small number of solar-specific fields in JNB; the pipeline fetches the job, fills the form, and attaches the completed PDF and a field log back to the JNB job record.

---

## Setup

**Requirements:** Python 3.12+, ngrok (for local webhook testing)

```bash
git clone https://github.com/mavaylon1/ecosolar_pipeline.git
cd ecosolar_pipeline

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

The pipeline reads `JOBNIMBUS_API_KEY` from `~/.env`. Make sure that file exists:

```
JOBNIMBUS_API_KEY=your_key_here
```

---

## Running Locally

**Start the webhook server:**
```bash
python server.py
# Running on http://127.0.0.1:8000
```

**Expose it publicly via ngrok (second terminal):**
```bash
ngrok http 8000
# Forwarding: https://abc123.ngrok-free.app → http://localhost:8000
```

**Health check:**
```bash
curl https://abc123.ngrok-free.app/health
# {"status": "ok"}
```

**Manually trigger the pipeline against a real JNB job:**
```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"jnid": "<job-jnid>"}'
```

On success, a filled PDF and field log are attached to the JNB job record.

---

## Running Tests

### Tier 1 — Unit tests (no JNB, runs in under 1s)
```bash
pytest tests/test_unit.py -v
```

### Tier 2 — Integration (read-only JNB, generates PDF locally)
```bash
pytest tests/test_local_preview.py -s --jnid <jnid>
```

Output files are saved to `output/` (gitignored):
- `output/permit_data_<jnid>.json` — transformed data fed into the PDF filler
- `output/field_log_<jnid>.txt` — human-readable mapping of JNB fields → PDF fields
- `output/preview_<jnid>.pdf` — the filled PDF, open to visually verify

### Tier 3 — End-to-end (creates and archives JNB records, manual only)
```bash
# Direct webhook POST — tests everything except the JNB automation trigger
pytest tests/test_e2e.py

# Full trigger chain — creates a job so JNB fires the webhook automatically on creation
pytest tests/test_e2e.py --full-trigger
```

> Requires the JNB automation rule to be configured: **Trigger = Job Created → Action = Webhook → your URL**.
> Tier 3 creates real JNB records and archives them on cleanup. Run sparingly — on initial setup, after infrastructure changes, or before deploying to production.

---

## Adding a New City Form

1. Create `forms/<city_name>/` directory
2. Add `template.pdf` — the city's fillable PDF
3. Add `mapping.json` — maps schema keys to PDF field names (use `forms/garden_grove/mapping.json` as a template)
4. Add `README.md` — documents every field source, calculation, and controlled value (use `forms/garden_grove/README.md` as a template)
5. Register the city in `forms/registry.py`:
   ```python
   "new city name": {
       "mapping": _FORMS_DIR / "new_city_name" / "mapping.json",
       "template": _FORMS_DIR / "new_city_name" / "template.pdf",
   }
   ```
6. Add any city-specific transformer logic to `pipeline/transformer.py`

---

## Project Structure

```
server.py                    Flask webhook server (POST /webhook, GET /health)
pipeline/
  jnb_client.py              All JNB API calls — fetch, create, archive, attach
  transformer.py             JNB job + contact → permit data schema
  runner.py                  Orchestrates pipeline, generates and attaches field log
forms/
  registry.py                Maps jurisdiction name → mapping + template
  fill.py                    PDF AcroForm filler (PyMuPDF)
  garden_grove/
    template.pdf             Garden Grove permit application PDF template
    mapping.json             Schema key → PDF field name mapping
    README.md                Field source documentation for Garden Grove
reports/                     Placeholder for portal report outputs (Phase 3)
tests/
  test_unit.py               Tier 1 — unit tests, no external calls
  test_local_preview.py      Tier 2 — read-only JNB integration test
  test_e2e.py                Tier 3 — full pipeline end-to-end test
conftest.py                  Shared pytest CLI options
.github/workflows/daily.yml  Tiers 1 & 2 run daily at 9am PT via GitHub Actions
output/                      Local test artifacts (gitignored)
```

---

## CI

GitHub Actions runs Tier 1 and Tier 2 daily at 9am PT. Trigger a run manually from the **Actions** tab → **Daily Tests** → **Run workflow**.

Required GitHub secret: `JOBNIMBUS_API_KEY`
Optional GitHub variable: `PREVIEW_JNID` (defaults to a stable Garden Grove job)
