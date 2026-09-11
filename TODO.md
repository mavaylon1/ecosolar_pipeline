# TODO

## Text cutoff / overflow in filled PDF fields

**Problem:** some filled fields visually cut off or overflow their box — e.g. "Description of
Work" wraps across multiple PDF fields but each line's font auto-sizes independently, so lines
end up at inconsistent sizes and can overflow (requires horizontal scroll to read). "License Type"
and similar single-line fields can also overflow if the box is narrow relative to the content.

**Root cause:** `forms/fill.py` never sets a font size when filling a field — it just uses
whatever font-size setting (auto or fixed) the original PDF's author left on that widget. Auto-size
doesn't always shrink enough to truly fit, and our multi-line wrap approach
(`_wrap_to_fields` in `forms/fill.py`, character-count-based via `textwrap.wrap`) doesn't account
for actual proportional font-metrics width, so a "line" that fits the character-count budget can
still be visually too wide or too narrow for its box, and each wrapped field auto-sizes
independently of its neighbors.

**Approach decided:** deterministic width-check, not agentic/visual (LLM-render-and-look) evaluation.
Reasoning: overflow is a measurable fact (rendered text width at a given font size vs. box width),
not a judgment call — PyMuPDF can compute this directly from font metrics. A deterministic check is
instant, free, and 100% consistent; an agentic visual check would be slower, cost money per run, and
could misjudge borderline cases. Reserve agentic/visual checks (if ever) for one-time spot review,
not a repeatable QA step.

**Plan (not yet built):**
- Add a check to `forms/fill.py` (or a wrapper used alongside it) that, for every field actually
  filled, measures the rendered text width (via PyMuPDF font metrics, at whatever font size will
  actually be used) against the widget's box width, and flags it as a new issue type (e.g.
  `"text_overflow"`) in the existing `issues` list — same mechanism already used for
  missing-required-fields, so no new reporting path needed.
- For the multi-line wrap case specifically, consider switching wrapped fields to a **fixed** font
  size (like the Anaheim/Fullerton/LA County conversions already do — `text_fontsize = 9`) instead
  of leaving them on auto, so all lines render consistently, then size `wrap_width` in
  `mapping.json` to fit that fixed size and box width instead of an arbitrary character count.
- Decide whether this lives only in `forms_in_progress`/experimental work first, or goes straight
  into production `forms/fill.py` since Garden Grove's live form could have the same issue and
  nobody's checked (checked once, 2026-08-28 — production's own "Class" field had plenty of
  margin, but that's one field on one form, not a general clearance).

**Partial mitigation so far (2026-09-11), not the general fix above:** `forms/fill.py`'s
`_build_updates` now supports an explicit per-field `fontsize` override (previously only
multi-field wrap groups had this), and a manual margin-recomputation audit (see
`GUARDRAILS.md` rule 5) was used to find and hand-fix specific known-bad fields — Garden
Grove declaration's "License Class", Westminster's "License Type" and "License Class and No",
Fullerton's "Contractor State Contr Number" and "Contractor Phone". This caught real instances
but is still a one-off patch per field found, not the automated check described above — a new
field with this problem would still slip through silently.

---

## `existing_solar_on_roof` can silently end up unset on the filled PDF

**Problem:** A live job (`132f8a31349541118fa4fb380e9ac75c`, "Emmanuel Cruz ADU") has JNB's
`Existing_panels` custom field storing the raw value `"0"` instead of `"Yes"`/`"No"`. The pipeline
assumes this field is always `"Yes"` or `"No"` end to end:
- `pipeline/transformer.py` only substitutes a default (`"No"`) when the field is entirely absent —
  not when it's present but holds an unrecognized value like `"0"`.
- `forms/garden_grove/mapping.json` maps it to a PDF **radio button**
  (`solar.existing_solar_on_roof`, `type: radio`).
- `forms/fill.py`'s radio handling compares the value against the button's "on" text; if it doesn't
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
logged) and/or have `forms/fill.py`'s radio handling raise a `FillIssue` when a non-empty value
doesn't match any known on/off state, instead of silently leaving the button unset.

---

(Add future items below this line.)
