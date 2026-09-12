# EcoSolar Permit Pipeline

Automated pipeline that fills city permit application PDFs using job data from JobNimbus. An engineer fills a small number of solar-specific fields in JNB; the pipeline fetches the job, fills the form, and attaches the completed PDF and a field log back to the JNB job record.

There's no live service — this runs on demand today, and will eventually run from a scheduled
(cron) script that pulls jobs, checks status, and fills forms in a batch. That script doesn't
exist yet; see `docs/ROADMAP.md`.

---

## Setup

**Requirements:** Python 3.12+

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

`pipeline` and `forms` live under `src/` — `conftest.py` puts `src/` on `sys.path` for tests
automatically. Running any script under `src/` directly does the same via its own
`sys.path.insert(...)` line, so no separate install step is needed.

---

## Running It

There's no server to start. To process one job right now, call the pipeline function directly:

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'src')
from pipeline.runner import run_pipeline
run_pipeline('<job-jnid>')
"
```

This fetches the job + contact from JNB, fills the right city's PDF, and attaches the filled
PDF and a field log back to the JNB job record.

To preview a fill without attaching anything back to JNB (useful while developing a mapping),
use the Tier 2 test below instead — it saves its output locally to `output/` for inspection.

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

---

## Adding a New City Form

New cities are drafted and tested in `forms_in_progress/` first, **not** added directly to
`forms/` — see `forms_in_progress/README.md` for that recipe (one shared registry/data-pull/fill
pipeline, not a copy-pasted script per city). `forms/` holds only cities that have already been
tested against real JNB data and are ready for production use.

Once a `forms_in_progress/` city is confirmed accurate, promoting it means:
1. Move its `template.pdf` + `mapping.json` from `forms_in_progress/<city>/` into `forms/<city>/`
2. Add a `README.md` documenting every field source, calculation, and controlled value (use
   `forms/garden_grove/README.md` as a template)
3. Register it in `src/forms/registry.py`:
   ```python
   "new city name": {
       "mapping": _FORMS_DIR / "new_city_name" / "mapping.json",
       "template": _FORMS_DIR / "new_city_name" / "template.pdf",
   }
   ```
4. Add any city-specific transformer logic to `src/pipeline/transformer.py`

`src/forms/registry.py` currently supports only one form per jurisdiction — Huntington Beach and
Westminster each need two, so that needs generalizing before either can be promoted as-is (see
`docs/ROADMAP.md`).

---

## Project Structure

```
src/                          All code. Nothing outside src/ is imported as Python - forms/,
                               forms_in_progress/, etc. below hold data (PDFs, mapping.json),
                               not code, even though some share a name with a src/ package.
  pipeline/
    jnb_client.py              All JNB API calls — fetch, create, archive, attach
    transformer.py             JNB job + contact → permit data schema
    runner.py                  run_pipeline(jnid) — fetch, fill, attach, for one job
  forms/
    registry.py                Maps jurisdiction name → mapping + template (in the root forms/)
    fill.py                    PDF AcroForm filler (PyMuPDF)
  forms_in_progress/           Draft-city driver scripts — see forms_in_progress/README.md
docs/                          README.md stays at root (GitHub renders it as the repo homepage);
                               everything else lives here:
  ROADMAP.md                   Phase plan
  GUARDRAILS.md                Conventions every city/form mapping must follow — read before
                                writing or reviewing one
  TODO.md                      Known issues not yet fixed
  PENDING_FORMS_CONVERSION_NOTES.md   Hand-conversion technique reference (flat PDF → fillable)
forms/                         DATA ONLY — cities tested and ready for production use
  garden_grove/
    template.pdf                Garden Grove permit application PDF template
    mapping.json                Schema key → PDF field name mapping
    README.md                   Field source documentation for Garden Grove
forms_in_progress/              DATA ONLY — draft cities being tested against real JNB data
                                 before promotion to forms/, plus output/ (generated, safe to
                                 delete) — see forms_in_progress/README.md
ask_ecosolar/                   Forms with a mapping drafted (or moot) but blocked on a
                                 question only EcoSolar can answer — see ask_ecosolar/README.md
not_possible_forms/             Structurally blocked (data doesn't exist in JNB, or a scanned
                                 PDF with no text layer) — see not_possible_forms/README.md
reports/                        Placeholder for portal report outputs (Phase 3)
tests/
  test_unit.py                  Tier 1 — unit tests, no external calls
  test_local_preview.py         Tier 2 — read-only JNB integration test
conftest.py                     Puts src/ on sys.path for every test; shared pytest CLI options
output/                         Local test artifacts (gitignored)
```
