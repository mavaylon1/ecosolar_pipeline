# Roadmap

## Phase 1 — Garden Grove (current)

Single-city PDF pipeline fully operational, invoked directly (no server, no webhook — see the
root `README.md`'s "Running It" section):
- `pipeline.runner.run_pipeline(jnid)` fetches the job + contact, fills Garden Grove's form,
  attaches the filled PDF and a field log back to the JNB job record
- Two-tier test suite (Tier 1 unit, Tier 2 read-only JNB integration)

**Remaining to close out Phase 1:**
- ~~Confirm exact JNB API key names for the 4 engineer-entered custom fields~~ — confirmed live 2026-07-12: `Job_description`, `Structure`, `Existing_panels`, `System_kw_ac`
- Mark those 4 fields as required in JNB so they are populated before a job reaches Permit status
- Build the Phase 2 scheduled runner below, so `run_pipeline` stops being invoked by hand per job

---

## Phase 2 — Scheduled (Cron) Runner

Replace manual per-job invocation with a script that runs on a schedule, checks JNB for jobs
ready to process, and runs the pipeline for each one automatically. Not started yet — this is
the next real infrastructure piece. No server or webhook involved; this runs wherever a
scheduler (cron or equivalent) is available.

**What it needs to do:**
- Query JNB for jobs in the right status/state to process (replaces "a webhook fires on status
  change" as the trigger)
- Skip jobs already processed, so re-running doesn't re-fill and re-attach a PDF every time
- Match each job to its city's form (`src/forms/registry.py`)
- Run the pipeline, attach PDF + field log
- Structured error handling — on failure, post a note to the JNB job explaining what went wrong
  so Alyssa knows why no PDF was attached, instead of failing silently
- Add retry logic for transient JNB API failures

**Definition of done:** A job reaching the right status gets its permit PDF filled and attached
without anyone running anything by hand.

---

## Phase 3 — Multi-City PDFs and Portal Reports

Expand coverage to all cities EcoSolar operates in.

**Current state (2026-09-12):** `forms_in_progress/` is the active staging pipeline for this
phase — 14 cities now have real field mappings tested against live JobNimbus data (Fountain
Valley, Huntington Beach, Westminster, Anaheim ×2 forms, Fullerton, LA County, Corona, Pomona,
Stanton, Yorba Linda, Redlands, San Diego County, Long Beach, Irvine), alongside Garden Grove's
own production form. See `forms_in_progress/README.md` for the architecture (one shared
registry/data-pull/fill pipeline, not a copy-pasted script per city).

`pending_forms/` and `pending_forms_fillable/` have both been fully retired (2026-09-12) — every
city's source PDF has either been mapped and tested (above), is structurally blocked in
`not_possible_forms/`, or is blocked on an EcoSolar decision in `ask_ecosolar/`. The hand-
conversion technique notes from `pending_forms_fillable/` live on at
`docs/PENDING_FORMS_CONVERSION_NOTES.md`, for the next time a city's source PDF turns out flat.
- `not_possible_forms/` — structurally blocked, not a mapping problem (Anaheim B701 needs data
  that doesn't exist in JNB; one of Orange's two PDFs is a scanned image with no text layer).
  See `not_possible_forms/README.md`.
- `ask_ecosolar/` — mapping work is either done or moot, but blocked on a question only EcoSolar
  can answer: Kern County (zero job history to test against), Long Beach app-011 (unclear if
  it's even the right document for solar permits), Orange's Express Checklist (~150 fields are
  per-job engineering self-certifications, not JNB data — only a small ID block is automatable).
  See `ask_ecosolar/README.md`.

Read **`GUARDRAILS.md`** before writing or reviewing any new mapping — it captures the
conventions every city mapping so far has had to learn the hard way (never auto-fill someone
else's legal declaration, don't guess unverified defaults, verify checkboxes by position not
name, real overflow-margin checks, etc.).

**Known gap blocking promotion to production:** `src/forms/registry.py` only supports one form per
jurisdiction today. Huntington Beach and Westminster each need 2 forms registered per city —
this needs to be generalized before any `forms_in_progress` city can graduate to `forms/`.

**Additional PDF cities:**
- Each promoted city follows the same pattern: `forms/<city>/template.pdf`, `mapping.json`,
  `README.md` (see `forms/garden_grove/` as the reference)
- Transformer may need city-specific logic (different field names, different controlled values)
- Target: 80% field coverage per form — remaining fields flagged in the field log as manual

**Portal reports:**
- Some cities use web portals instead of PDFs (no fillable form)
- Output is a structured report (PDF or formatted doc) listing every field and its value so the permit coordinator can copy-paste into the portal without looking anything up
- Lives in `reports/` — separate pipeline from the PDF filler, same data source
- Template per city: field label, value, source, any notes

**Shared infrastructure:**
- The transformer, JNB client, and field log are already city-agnostic
- Registry-based routing needs multi-form-per-city support before it "just handles" new cities
  (see gap above)
- Consider a coverage dashboard: for each city form, what % of fields are auto-filled vs. manual
- Need a real city/address → county mapper. Some forms are county-level, not city-level (e.g.
  LA County's declaration applies to unincorporated territory, which isn't a JNB `city` value at
  all — matching the incorporated City of Los Angeles isn't right either, since it has its own
  building dept separate from the county). Current stopgap in
  `src/forms_in_progress/registry.py`'s `la_county` entry: a hardcoded list of known unincorporated
  community names (Rowland Heights, Hacienda Heights) tried in order. Needs replacing with an
  actual address/zip → county lookup before this scales past one manually-curated example.

---

## Phase 4 — Agentic Error Investigation

When the pipeline fails, instead of just logging the error, trigger an AI agent to investigate and report.

**What the agent does:**
- Receives the error, the field log, and the raw JNB job data as context
- Identifies the likely cause (missing field, wrong format, unrecognized value, API error)
- Generates a plain-English diagnosis: *"Job abc123 failed because `system_kw_ac` contains '7.2 kW' (string with units) instead of '7.2' (number). The valuation calculation could not parse it."*
- Posts the diagnosis as a note on the JNB job so Alyssa and the engineer see it immediately

**Implementation:**
- Built on the Claude API (Anthropic SDK) with tool use
- Agent tools: fetch JNB job, read field log, inspect transformer output
- Report-only to start — agent diagnoses but does not auto-fix or write back to JNB
- Future: agent can suggest a corrected value and request human approval before retrying

**Why the current architecture supports this:**
- The field log is already the right context package — it documents every field attempted, what was found, and what failed
- The pipeline already has structured logging with job IDs and error messages
- Adding the agent is a new error handler layer on top of the existing pipeline, not a rewrite

**Guardrails:**
- Agent never writes to JNB without human approval
- All agent actions logged alongside the field log
- Escalation path: if agent cannot diagnose, it flags the job for manual review
