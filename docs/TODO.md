# TODO

## Text cutoff / overflow in filled PDF fields

**Status: general automated check built (2026-09-12).** `src/forms/fill.py`'s `_apply()` now
computes the real margin (usable box width minus rendered text width at the actual font used) for
every filled text field and flags anything under 3pt — negative margin (genuine overflow) is an
`"error"` (flips the form's status to `needs_review`), a thin-but-still-fitting margin is a
`"warning"` (worth a look, not a failure). This runs automatically on every `fill_pdf_form()` call,
for every city, with no separate script to remember to run. Multi-field wrap groups
(`pdf_field_names`) also gained a per-mapping `fontsize` override (previously hardcoded to 9pt with
no way to change it — a `wrap_width` key existed in a few mappings but was never actually read by
the code, silently doing nothing) and single fields gained a `max_fontsize` override (caps the
auto-fit ceiling below the default 11pt, for fields where 11pt leaves razor-thin margin even though
it technically fits).

**Real bugs this caught and fixed, same pass:** Huntington Beach's "Scope of Work" was rendering
at 6pt and still overflowing by ~517pt — a full paragraph crammed into one non-wrapping single-line
field, visibly cut off mid-sentence. Split into 3 stacked fields at 6.5pt. Westminster's
"Description of Work" was silently dropping the tail of the text off the end of its 2-field wrap
(hardcoded 9pt left no room) — fixed by lowering to 8pt, which fits both lines cleanly. Fullerton's
"Project Address" was passing with 0.3pt of margin — the old check didn't catch this at all, since
it only fired on literal overflow, not "barely made it." Capped with `max_fontsize: 9` for real
headroom, while auto-shrink below that still protects a longer future address.

**Known remaining case, not fixable by any of the above:** Fullerton's "License Class" (9pt-wide
table cell — no font size fits 3+ characters, left unmapped) and "Phone No" (27pt-wide cell, full
number forced in at 3.5pt) sit inside a hard-bordered printed table in the city's own PDF. Unlike
Huntington Beach, there's no blank page space to extend a widget into — growing either box would
cross the printed column divider into the neighboring cell. The only real fix would be editing the
city's own table layout (moving the printed divider lines), not a mapping or fill-engine change.
Left as documented in `forms_in_progress/fullerton/mapping.json`'s `_note` rather than forced.

---

## `existing_solar_on_roof` can silently end up unset on the filled PDF

**Problem:** A live job (`132f8a31349541118fa4fb380e9ac75c`, "Emmanuel Cruz ADU") has JNB's
`Existing_panels` custom field storing the raw value `"0"` instead of `"Yes"`/`"No"`. The pipeline
assumes this field is always `"Yes"` or `"No"` end to end:
- `src/pipeline/transformer.py` only substitutes a default (`"No"`) when the field is entirely absent —
  not when it's present but holds an unrecognized value like `"0"`.
- `forms/garden_grove/mapping.json` maps it to a PDF **radio button**
  (`solar.existing_solar_on_roof`, `type: radio`).
- `src/forms/fill.py`'s radio handling compares the value against the button's "on" text; if it doesn't
  match (e.g. `"0"`), it just leaves the radio unselected — no error or warning is raised.

**Impact:** the field log reports this as "found" (it's not empty), so nothing flags that the value
is unrecognized. The permit PDF can go out with this question silently left blank.

**Not yet investigated:**
- Why this job has `"0"` instead of `"Yes"`/`"No"` — two candidate explanations, unconfirmed:
  1. `Existing_panels` might be configured as a Boolean-type JNB custom field (which returns `0`/`1`)
     rather than the Text/Options type the rest of the pipeline assumes.
  2. This job may predate the 4 custom fields being added to JNB (2026-05-29) and never got
     backfilled with real data.
- Whether other live jobs show the same pattern, or if this one job is an outlier.

**Plan (not yet built):** once the cause is confirmed, either normalize unrecognized values in the
transformer (e.g. treat anything other than an exact "Yes" match as "No", with the raw value still
logged) and/or have `src/forms/fill.py`'s radio handling raise a `FillIssue` when a non-empty value
doesn't match any known on/off state, instead of silently leaving the button unset.

---

(Add future items below this line.)
