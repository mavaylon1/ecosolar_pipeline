# Roadmap

## Phase 1 — Garden Grove (current)

Single-city PDF pipeline fully operational:
- Webhook server receives JNB job trigger
- Transformer maps JNB fields to permit data schema
- PDF filler populates Garden Grove application form
- Filled PDF and field log attached back to JNB job record
- Three-tier test suite with daily CI on Tiers 1 and 2

**Remaining to close out Phase 1:**
- ~~Confirm exact JNB API key names for the 4 engineer-entered custom fields~~ — confirmed live 2026-07-12: `Job_description`, `Structure`, `Existing_panels`, `System_kw_ac`
- Mark those 4 fields as required in JNB so they are populated before a job reaches Permit status
- Run full Tier 3 end-to-end test
- Set up JNB automation rule: Trigger = Status Changed → Permit → Action = Webhook

---

## Phase 2 — Production Deployment

Move from ngrok + local machine to an always-on hosted service.

**Infrastructure:**
- Deploy to Railway (~$5/month). Server code requires no changes — only the webhook URL changes in JNB.
- Set `JOBNIMBUS_API_KEY` as a Railway environment variable
- Update the JNB automation rule (Status Changed → Permit → Webhook) to point at the Railway URL instead of ngrok

**Hardening:**
- Add webhook signature verification if JNB supports it (prevents unauthorized triggers)
- Add retry logic for transient JNB API failures
- Structured error reporting — on pipeline failure, post a note to the JNB job explaining what went wrong so Alyssa knows why no PDF was attached
- Monitor Railway logs; set up email alert on repeated failures

**Definition of done:** Pipeline runs without any local machine involvement. Alyssa changes a job status in JNB and the filled PDF appears on the job within 30 seconds.

---

## Phase 3 — Multi-City PDFs and Portal Reports

Expand coverage to all cities EcoSolar operates in.

**Current state (2026-09-11):** `forms_in_progress/` is the active staging pipeline for this
phase — 6 cities now have real field mappings tested against live JobNimbus data (Fountain
Valley, Huntington Beach, Westminster, Anaheim, Fullerton, LA County), alongside Garden
Grove's own production form. See `forms_in_progress/README.md` for the architecture (one
shared registry/data-pull/fill pipeline, not a copy-pasted script per city) and the recipe for
onboarding what's left, currently split across three folders by readiness:
- `pending_forms_fillable/` — already fillable, no mapping written yet (fastest path): Irvine,
  Kern County, Long Beach (2 forms), Redlands, San Diego County, Stanton, Yorba Linda, Orange
  (checklist form).
- `pending_forms/` — not fillable yet, needs hand-conversion first: Anaheim B705, Corona,
  Pomona.
- `not_possible_forms/` — structurally blocked, not a mapping problem (Anaheim B701 needs data
  that doesn't exist in JNB; Orange's other PDF is a scanned image with no text layer). See
  `not_possible_forms/README.md`.

Read **`GUARDRAILS.md`** before writing or reviewing any new mapping — it captures the
conventions every city mapping so far has had to learn the hard way (never auto-fill someone
else's legal declaration, don't guess unverified defaults, verify checkboxes by position not
name, real overflow-margin checks, etc.).

**Known gap blocking promotion to production:** `forms/registry.py` only supports one form per
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
  `forms_in_progress/registry.py`'s `la_county` entry: a hardcoded list of known unincorporated
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
