# Roadmap

## Phase 1 — Garden Grove (current)

Single-city PDF pipeline fully operational, invoked directly (no server, no webhook — see the
root `README.md`'s "Running It" section):
- `pipeline.runner.run_pipeline(jnid)` fetches the job + contact, fills every form registered
  for Garden Grove, attaches each filled PDF and a VERIFY CSV back to the JNB job record
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
- Match each job to its city's form(s) (`src/forms/registry.py`'s `find_forms(city)`)
- Run the pipeline, attach PDF + VERIFY CSV per form
- Structured error handling — on failure, post a note to the JNB job explaining what went wrong
  so Alyssa knows why no PDF was attached, instead of failing silently
- Add retry logic for transient JNB API failures

**Definition of done:** A job reaching the right status gets its permit PDF filled and attached
without anyone running anything by hand.

---

## Phase 3 — Multi-City PDFs and Portal Reports

Expand coverage to all cities EcoSolar operates in.

**Current state (2026-09-20): done, for every city with a usable source PDF.** 15 cities now
live directly in `forms/` with real field mappings tested against live JobNimbus data (Garden
Grove ×2 forms, Fountain Valley, Huntington Beach ×2, Westminster ×2, Anaheim ×2, Fullerton, LA
County, Corona, Pomona, Stanton, Yorba Linda, Redlands, San Diego County, Long Beach, Irvine).
There's no separate staging area anymore - `forms/` holds every city, discovered by folder
convention (`src/forms/registry.py`'s `find_forms(city)`, no static list to keep in sync). The
one-form-per-jurisdiction limitation that used to block multi-form cities from going live is
resolved - a city folder can hold any number of `mapping*.json` files and every one of them
gets filled and attached independently.

`pending_forms/`, `pending_forms_fillable/`, and `forms_in_progress/` have all been fully
retired - every city's source PDF has either been mapped and tested (above), is structurally
blocked in `not_possible_forms/`, or is blocked on an EcoSolar decision in `ask_ecosolar/`. The
hand-conversion technique notes from `pending_forms_fillable/` live on at
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

**Additional PDF cities:**
- Each new city follows the same pattern: `forms/<city>/<template>.pdf`, `mapping.json` (with a
  `"template"` key naming its own PDF), `README.md` (see `forms/garden_grove/` as the reference)
- Transformer may need city-specific logic (different field names, different controlled values)
- Target: 80% field coverage per form — remaining fields flagged in the VERIFY CSV as manual

**Portal reports:**
- Some cities use web portals instead of PDFs (no fillable form)
- Output is a structured report (PDF or formatted doc) listing every field and its value so the permit coordinator can copy-paste into the portal without looking anything up
- Lives in `reports/` — separate pipeline from the PDF filler, same data source
- Template per city: field label, value, source, any notes

**Shared infrastructure:**
- The transformer, JNB client, and VERIFY reporting are already city-agnostic
- Folder-convention routing already handles any number of forms per city with no code changes
- Consider a coverage dashboard: for each city form, what % of fields are auto-filled vs. manual
- Need a real city/address → county mapper. Some forms are county-level, not city-level (e.g.
  LA County's declaration applies to unincorporated territory, which isn't a JNB `city` value at
  all — matching the incorporated City of Los Angeles isn't right either, since it has its own
  building dept separate from the county). Current stopgap: `forms/la_county/mapping.json`
  declares a `"cities"` list of known unincorporated community names (Rowland Heights, Hacienda
  Heights) that route to it. Needs replacing with an actual address/zip → county lookup before
  this scales past two manually-curated examples.

---

## Phase 4 — Agentic Issue Triage

The pipeline itself rarely "fails" anymore (see `docs/GUARDRAILS.md` — only a genuine
infrastructure problem raises; missing data or a bad mapping just gets noted in the VERIFY CSV
instead of blocking anything). What's worth automating next is triaging *those* notes, not
error recovery: every attached VERIFY CSV already sorts issues into `missing_data` (needs a
human to type in a value), `needs_visual_check` (open the PDF and look), and `mapping_error`
(something's actually broken and needs an engineer) - an agent could read that CSV and do the
first pass of that triage instead of a person scanning it manually.

**What the agent does:**
- Receives a job's attached VERIFY CSV(s) and the raw JNB job data as context
- For each `mapping_error` row specifically, identifies the likely root cause (wrong PDF field
  name, a spec that's missing something it needs) and generates a plain-English diagnosis
- Posts the diagnosis as a note on the JNB job so whoever's reviewing it doesn't have to
  re-derive what the CSV already implies

**Implementation:**
- Built on the Claude API (Anthropic SDK) with tool use
- Agent tools: fetch JNB job, read the attached VERIFY CSV(s), inspect the relevant mapping.json
- Report-only to start — agent diagnoses but does not auto-fix or write back to JNB
- Future: agent can suggest a corrected mapping and request human approval before retrying

**Why the current architecture supports this:**
- The VERIFY CSV is already the right context package — it documents every field attempted,
  its source, its value, and a category for anything that needs attention
- Adding the agent is a new layer that reads what's already attached, not a rewrite

**Guardrails:**
- Agent never writes to JNB without human approval
- All agent actions logged alongside the VERIFY CSV they're triaging
- Escalation path: if agent cannot diagnose a `mapping_error`, it flags the job for manual review
