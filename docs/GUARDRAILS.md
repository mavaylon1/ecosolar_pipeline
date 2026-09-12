# Guardrails

Conventions that apply across every city/form in this pipeline — production (`forms/`) and
staging (`forms_in_progress/`) alike. Read this before writing or reviewing a new field mapping.
Each rule below was learned from a real bug caught during Garden Grove/Fountain Valley/Huntington
Beach/Westminster/Anaheim/Fullerton QA — not theoretical.

---

## 1. Never fill someone else's first-person legal declaration

Some form sections are the *property owner's* own sworn statement ("I, as owner of the
property..."), not the contractor's. EcoSolar is always the contractor — it should never check
a box or print a name inside a declaration that only the actual owner is legally entitled to make,
even if the "obviously correct" answer seems predictable.

- **Owner-Builder Declaration** sections (Westminster, Garden Grove, LA County): leave every
  checkbox and "Owner Print Name" field unmapped entirely.
- **Lobbyist Ordinance Certification** (LA County): a conditional certification ("unincorporated
  LA County only") we can't universally assert applies — left unmapped.

Caught because an earlier draft of Westminster's mapping checked this box on the owner's behalf;
Garden Grove's declaration had the identical bug.

## 2. Don't guess an unverified default

If a piece of information genuinely isn't tracked anywhere (e.g. whether a job has a construction
lending agency, a contractor's business address), leave the field blank/missing rather than
filling in a "probably fine" placeholder like `"N/A"`. A missing-required-field flag in the fill
report is useful signal; a guessed value that happens to be wrong is a silent, undetectable error
on a real permit document.

## 3. Signature fields always stay blank

Only "Print Name" fields get filled with real text. Anything labeled "Signature" is left blank for
physical/wet signing — regardless of what a one-off dummy-fill script did for visual QA purposes
(dummy scripts optimize for "does this render," not "is this the correct real-data behavior").

## 4. Verify checkbox identity by position, not by name

Generically-named checkboxes (`Check Box1`, `Check Box2`, ...) tell you nothing about which real
answer they represent, and a checkbox's *internal field name* can also be flatly wrong relative to
its position on the page (e.g. a checkbox named "licensed pursuant to the Contractors State
License Law" that is actually, by its y-coordinate, the "I am exempt under Sec.___" checkbox).
Always confirm via `page.search_for("label text")` coordinates cross-referenced against the
checkbox's own `rect`, not by field name or assumed document order.

## 5. A margin warning still needs a visual check, in both directions

`src/forms/fill.py`'s `_apply()` automatically flags any field with under 3pt of margin (real
rendered text width vs. usable box width, at the actual font used) — an `"error"` for genuine
negative-margin overflow, a `"warning"` for anything thinner than that. This runs on every fill,
for every city, with no separate audit script needed (fixed 2026-09-12 - it used to only catch
literal overflow, so a field passing with 0.3pt to spare reported zero issues).

The font-metric estimate isn't a perfect match for how a PDF viewer actually lays out glyphs in
either direction, though, so a flag still isn't the final word:
- A `"warning"` can be a false positive — Pomona's "Solar Kilowatts" and Redlands' "Company
  license class" both flag under 3pt but render with comfortable clearance on inspection. Don't
  assume a warning means a real problem without looking.
- A `"passed"` status with zero issues can still visually overflow in the rare case font metrics
  underestimate real glyph width. When auditing a form for cutoff/spacing issues that the automated
  check didn't catch, render it and look — don't stop at the issues list alone.

When a box is genuinely too narrow for its content:
- Try a tighter format first (e.g. `"C10,C46"` instead of `"C10, C46"`) if the value is one we
  control the formatting of.
- Force an explicit, deliberately-safe `fontsize` in the mapping (`_build_updates` honors this for
  both single fields and multi-field wrap groups) rather than relying on auto-shrink's
  just-barely-fits behavior.
- If nothing fits at a legible size, or fitting would require truncating information in a way that
  misrepresents reality (e.g. showing only one of EcoSolar's two license classes), leave the field
  unmapped rather than forcing it. Document why in the mapping's `_note`.

## 6. Reuse over duplication

- Schema keys (`project.*`, `property.*`, `owner.*`, `contractor.*`, `workers_comp.*`,
  `business.*`, `solar.*`, `solar_use.*`, `reroof.*`, `city_license.*`) represent real-world facts
  and should be reused across every city's mapping that needs that same fact — don't invent a new
  key name per city for the same thing.
- Shared logic (pulling example jobs, building verify docs) lives once in
  `src/forms_in_progress/example_jobs.py` / `verify.py`, imported by every driver script. A per-city
  script that reimplements this logic independently is a sign it should be pulled into the shared
  module instead — this already happened once (`fill_plancheck.py` and `build_verify_docs.py` had
  two independently-drifting copies of the same source-of-truth table before being consolidated).
- Custom, one-off code is for genuine per-form edge cases only — e.g. the fix baked into
  `forms_in_progress/westminster/Building Permit Application_fixed.pdf`, which works around a real
  bug in Westminster's own PDF (one AcroForm field reused for three different address boxes; the
  one-time script that produced this fixed copy has since been retired, its job already done). It
  is not a shortcut around building the shared path properly.

## 7. A form that doesn't fit the schema might not belong yet

Not every city PDF is a "new solar installation" application. Anaheim's B701 (Permit Extension
Request) needs a city-issued permit number and a free-text reason — neither exists in JobNimbus,
and neither is knowable at job-creation time. Recognizing "this is fundamentally a different kind
of event than what the pipeline handles" and setting it aside (`not_possible_forms/anaheim/`,
see its README) is the right call, not a mapping problem to force a solution onto.

## 8. Never commit real customer data

`permit_data.json` files (one per city, in `forms_in_progress/`) hold real names, phones, emails,
and addresses pulled live from JobNimbus jobs — they're gitignored
(`forms_in_progress/*/permit_data.json`) and must stay that way. Regenerate via
`src/forms_in_progress/build_data.py` instead of sharing the file. Fabricated dummy data
("Jane Engineer"/"John Homeowner" style, e.g. in a QA render made while hand-converting a flat
PDF - see `docs/PENDING_FORMS_CONVERSION_NOTES.md`) is fine to commit — it was never real.

---

## Quality-check checklist for a new or changed form mapping

1. `build_data.py` then `run_all.py` — check `fill_reports.json` for that form's issues.
2. Recompute fit margin for every filled text field (see rule 5) — don't trust the pass/fail
   status alone.
3. Render at 150dpi for a full-page visual check; 400dpi crop-zoom on anything flagged or that
   looks tight/suspicious.
4. For any checkbox, confirm its identity by position (rule 4), not name.
5. Confirm against a **real** example job pulled live from JNB, not just dummy data — dummy data
   hid the owner-declaration bug's real-world implications and wouldn't have surfaced the license-
   class overflow the way an actual long value did.
