# EcoSolar Permit Pipeline

Automated pipeline that fills city permit application PDFs using job data from JobNimbus. An engineer fills a small number of solar-specific fields in JNB; the pipeline fetches the job, fills every form registered for that job's city, and attaches each filled PDF plus a VERIFY report back to the JNB job record.

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

This fetches the job + contact from JNB, resolves the job's city to every form registered for
it (a city can have more than one — e.g. Huntington Beach has a Solar application and an
Asbestos Disclosure), fills each one independently, and attaches each filled PDF plus a VERIFY
CSV (every field, its JNB source, its value, and a note if something needs attention) back to
the job. **Nothing here blocks** — a missing value or a mapping problem gets noted in the VERIFY
CSV for manual review, it never withholds an attachment. See `docs/GUARDRAILS.md` for why.

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
- `output/preview_<form>_<jnid>.pdf` — the filled PDF per form, open to visually verify
- `output/VERIFY_<form>_<jnid>.csv` — every field, its JNB source, its value, and any notes

---

## Adding a New City Form

No registry to update — a city's forms are just whatever `mapping*.json` files live in
`forms/<city>/`, discovered by convention:

1. Normalize the city name (lowercase, spaces → underscores) and create `forms/<that name>/`.
2. Add the fillable template PDF and a `mapping.json` (or `mapping_<name>.json` if this city
   will have more than one form — see Huntington Beach or Westminster for the pattern).
3. Add a `"template"` key to the mapping naming its PDF (same folder) — mappings are
   self-describing, nothing external links a mapping to its template.
4. If the job's real JNB `city` value won't match the folder name naturally (an unincorporated
   county's jobs come through under a community name, not the county's own name — see LA County
   and San Diego County for the pattern), add a `"cities"` key listing every JNB city value that
   should route here.
5. Add a `README.md` documenting every field source, calculation, and controlled value (use
   `forms/garden_grove/README.md` as a template).
6. Reuse existing schema keys (`project.*`, `property.*`, `owner.*`, `applicant.*`,
   `contractor.*`, `workers_comp.*`, `city_license.*`, `business.*`, `solar.*`, `solar_use.*`,
   `reroof.*`) wherever the new form asks for a fact another city's mapping already covers. If
   the form needs a genuinely new fact, add it once in `src/forms/example_jobs.py`'s
   `extend_permit_data()` and once in `src/forms/verify.py`'s `JNB_SOURCE` table — not per-city.

Read `docs/GUARDRAILS.md` before writing or reviewing any mapping — it captures conventions
every city mapping has had to learn the hard way (never auto-fill someone else's legal
declaration, don't guess unverified defaults, verify checkboxes by position not name, real
overflow-margin checks, etc.).

To test a new mapping against real JNB data before considering it done:
```bash
.venv/bin/python src/forms/build_data.py   # pulls a real example job per city, writes output/
.venv/bin/python src/forms/run_all.py       # fills every form, writes output/<city>/
```

---

## Project Structure

```
src/                          All code. forms/ below (no src/ prefix) is data - PDFs and
                               mapping.json - even though it shares a name with src/forms/.
  pipeline/
    jnb_client.py              All JNB API calls — fetch, create, archive, attach
    transformer.py             JNB job + contact → permit data schema
    runner.py                  run_pipeline(jnid) — fetch, fill every form for the city, attach
  forms/
    registry.py                find_forms(city) — folder-convention lookup, no static registry
    fill.py                    PDF AcroForm filler (PyMuPDF)
    verify.py                  Builds the VERIFY CSV (PDF field -> JNB source -> value -> note)
    example_jobs.py             Pulls a real example job from JNB for a city, for testing
    build_data.py               Driver: pulls one example job per city in forms/, writes output/
    run_all.py                  Driver: fills every form for every city, writes output/
docs/                          README.md stays at root (GitHub renders it as the repo homepage);
                               everything else lives here:
  ROADMAP.md                   Phase plan
  GUARDRAILS.md                Conventions every city/form mapping must follow — read before
                                writing or reviewing one
  TODO.md                      Known issues not yet fixed
  PENDING_FORMS_CONVERSION_NOTES.md   Hand-conversion technique reference (flat PDF → fillable)
forms/                         DATA ONLY — every city, ready for production use
  garden_grove/
    template.pdf                Garden Grove Plancheck PDF template
    mapping.json                Schema key → PDF field name mapping (+ "template" key)
    mapping_declaration.json    Garden Grove's second form (Declaration)
    README.md                   Field source documentation for Garden Grove
  <city>/                      Same pattern for every other city - mapping*.json + template(s)
ask_ecosolar/                  Forms with a mapping drafted (or moot) but blocked on a
                                question only EcoSolar can answer — see ask_ecosolar/README.md
not_possible_forms/            Structurally blocked (data doesn't exist in JNB, or a scanned
                                PDF with no text layer) — see not_possible_forms/README.md
reports/                       Placeholder for portal report outputs (Phase 3)
tests/
  test_unit.py                  Tier 1 — unit tests, no external calls
  test_local_preview.py         Tier 2 — read-only JNB integration test
conftest.py                     Puts src/ on sys.path for every test; shared pytest CLI options
output/                         Local test/preview artifacts, incl. PROGRESS.md (gitignored -
                                real customer data pulled live from JNB, never committed)
```
