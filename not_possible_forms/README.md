# not_possible_forms

Forms that can't currently be automated by this pipeline — not because of missing mapping work,
but for a structural reason that mapping work can't solve. Kept here (not deleted) in case the
blocking reason changes later.

## Anaheim — B701 (Permit Extension Request)

**Why it's blocked:** this form requests an extension on a permit that's *already been issued*,
not a new solar installation application. Two of its real fields have no possible data source in
JobNimbus:
- **List all Permit Numbers** — the city-assigned permit number doesn't exist until the city
  approves the original filing. It's not a JNB field; it comes back from the city, later than
  anything this pipeline currently touches.
- **State Reason for Requesting an Extension** — free text written per-request, situationally
  (e.g. "waiting on utility interconnection"), long after job creation. Not knowable in advance,
  not stored anywhere.

Everything else on the form (requester name/company/address/phone/email, job address) maps fine
to the same data every other form uses — it's specifically those two fields that block it.

**What would unblock it:** if EcoSolar starts tracking issued permit numbers in JobNimbus (e.g. a
custom field populated after city approval) and adopts a convention for extension requests
(perhaps a separate JNB record type or a note field), this could move to `pending_forms_fillable/`
— the widget placement (`B701_fillable.pdf`) is already done and verified clean.

**Files:** `B701-PERMIT EXTENSION REQUEST FORM_202508282224398561.pdf` (raw), `B701_fillable.pdf`
(hand-converted, widgets placed and verified), `B701_dummy_filled.pdf` (QA render),
`build_anaheim_b701.py` (regenerates the fillable copy from the raw original).

## Orange — Photovoltaic Permit Application

**Why it's blocked:** scanned image, no text layer at all. Every other flat-PDF conversion in
`pending_forms_fillable/` relied on `page.search_for("label text")` to find exact label positions
before placing a field next to it — that requires a real text layer, which this file doesn't have.
Coordinates would have to be eyeballed from the image directly, which is far more error-prone and
wasn't judged worth it for this pass.

Note: Orange has a *second* form — "Express Checklist for Residential Solar PV and ESS System" —
which is unrelated and already fillable; that one lives in `pending_forms_fillable/orange/` and is
not blocked. Don't confuse the two.

**What would unblock it:** either a genuinely scanned-PDF-capable conversion approach (OCR-assisted
coordinate finding, or just careful manual eyeballing against the rendered image), or asking the
city for a native fillable version if one exists.

**Files:** `Photovoltaic Permit Application 113022.pdf` (the scanned original — nothing else, since
no conversion was attempted).

## Uncategorized reference documents

**Why they're here:** `Structural Criteria for Residential29.pdf` and
`checklist for solar PV final draft26.pdf` aren't permit application forms tied to a specific
city — they read as general reference/checklist material. Not clear which jurisdiction (if any)
they belong to, or whether they're meant to be filled out at all vs. just read.

**Not necessarily blocked the way the two forms above are** — they may turn out to be entirely
fillable and mappable once someone identifies what they actually are and which city (if any) they
belong to. Filed here as "not in scope for now," not "structurally impossible."

**Files:** `Structural Criteria for Residential29.pdf`, `checklist for solar PV final draft26.pdf`
(both unmodified originals).
