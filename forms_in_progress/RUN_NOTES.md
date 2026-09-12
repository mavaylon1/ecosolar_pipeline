> Historical log from the first pass through all 6 forms — kept for context, not
> regenerated. For the current directory structure and how to run/extend this, see
> `README.md`. The scripts referenced below (`build_data.py`'s data, `run_fills.py`) have
> since been consolidated into `registry.py` + `build_data.py` + `run_all.py`.

# Initial fill-in test — results and open questions

Ran all 6 priority-city forms through the same fill mechanism Garden Grove's production form
uses (`forms/fill.py`), using one real job pulled live from JobNimbus (any job/contact — city
match wasn't the point here). Goal: confirm the fields actually pull, populate, and see what's
missing. Source: `forms_in_progress/build_data.py` (data), `forms_in_progress/*/mapping_*.json`
(field mapping), `forms_in_progress/run_fills.py` (runs the fill + prints/save a report).

Two real bugs were caught by actually running this against live data (details below) — both fixed.
One real defect in a city's own PDF was found that can't be fixed on our end.

---

## Garden Grove — Permit Declaration

**Marked required (assuming the form actually requires them — not fully confirmed):**
- Business Tax No, Address (contractor's), Policy No / Carrier / Expiration Date (workers' comp)

All 5 came back "missing" as expected — none of these have real static values defined yet.

**Assumed NOT required (so left out of the required check) — could be wrong:**
- ContractorAgent 1 — mapped to Allysa's name as a best guess, but genuinely unsure whose name
  belongs here (contractor's own agent? the applicant?). Filled it in and it visually looks fine,
  but the label itself is ambiguous.

**No clear JNB mapping, but plausible to add:**
- Business Tax No, contractor's business address, workers' comp carrier/policy/expiration — all
  need real values from Alyssa, not a JNB field at all.

---

## Fountain Valley — Permit Application

**Marked required:**
- Contractor email/address/city/state/zip, contractor license expiration, workers' comp
  carrier/expiration/policy/phone, city business license #/expiration — all 12 flagged, all came
  back missing as expected.

**Assumed NOT required — worth double-checking:**
- UNIT # — assumed optional since the sample job's `address_line2` was empty. Could be required
  for condos/multi-unit properties.
- TYPE OF CONSTRUCTION / OCCUPANCY GROUP / OCCUPANCY LOAD — left unmapped entirely (no JNB field),
  assumed the city doesn't actually need these filled for a simple solar permit. Not confirmed.

**No clear JNB mapping:**
- Same static-data gaps as Garden Grove above, plus Type of Construction/Occupancy
  Group/Occupancy Load if those turn out to matter.

---

## Huntington Beach — Photovoltaic Solar Permit Application

**Bug found and fixed:** the MFD/SFD checkboxes and the "Structural Calculations Yes/No"
checkboxes are 4 generically-named `Check Box1-4` widgets with no positional relationship to
their order in the file. I initially guessed wrong and it silently checked "Structural
Calculations: NO" instead of "SFD." Confirmed the fix by checking each widget's actual y-position
in the PDF and re-rendering — SFD now checks, Structural Calc stays untouched. **Lesson: don't
trust widget-order guesses for generically-named checkboxes — always check actual position.**

**Marked required:** Job Address, Property Owner's Name — both came back fine (no issues).

**Assumed NOT required, left unmapped:**
- Fee-schedule quantity boxes (Photovoltaic/Meter Size/EV Chargers/Sub-panel/PV Charge) — assumed
  these are always filled by staff/whoever calculates fees, not something we should auto-fill.
  Worth confirming that's actually true and not something the applicant is expected to enter.
- Energy Storage System fee qty — didn't map it even though `job.Number of Battery` could plausibly
  drive it, since it's the same fee-schedule pattern as the others. Flagged as a possible add.

---

## Huntington Beach — Asbestos / Permit Disclosure Form

Cleanest result — no issues. Project Address, Scope of Work, Applicant Name/Phone, and the
Owner/Owner-Builder/Contractor checkbox (always "Contractor") all filled and checked correctly.

**No clear JNB mapping:** none outstanding — everything on this short form either mapped cleanly
or is a staff/signing field that's correctly left blank.

---

## Westminster — Building Permit Application

**Bug found, NOT fixable on our end:** the "Address" field is the exact same AcroForm field for
the Owner, Applicant, and Contractor address blocks (confirmed — it's the only one of the
Name/Phone/Address/City/State/Zip fields on this form that DOESN'T get a `_2`/`_3` suffix for the
2nd/3rd occurrence). One value fills all three boxes. Currently mapped to the owner's address,
so the Applicant and Contractor rows will show the wrong address until/unless the city fixes
their PDF. Worth deciding whether to flag this for the city, or just pick whichever of the three
addresses is least likely to matter (arguably contractor, since applicant/owner are more likely
to be checked by the reviewer).

**Marked required:**
- Contractor city/state/zip, contractor license expiration, city license # — all came back missing
  as expected (no real values defined yet).

**Assumed NOT required:**
- Construction, Occupancy, Square Feet — left unmapped, assumed not applicable to solar-only work.
  Not confirmed with the city.

---

## Westminster — Building Permit Declaration

**Bug found and fixed:** a checkbox internally named `"licensed pursuant to the Contractors State
License Law"` is actually, by its position on the page, the **"I am exempt under Sec.___"**
checkbox in the Owner-Builder Declaration section — not a "contractor is licensed" checkbox as the
name suggested. Confirming this required checking the y-coordinate of every checkbox on the form
against the rendered page. Checking it was wrong (EcoSolar isn't claiming a licensing exemption) —
removed the mapping so it stays unchecked. Re-rendered and confirmed only "exclusively contracting
with licensed contractors" is checked now.

**Marked required:**
- Contractor license expiration, workers' comp carrier/policy number — all 3 came back missing
  as expected.

**No clear JNB mapping:** same workers' comp / license expiration gaps as the other forms.

---

## Summary of what's still needed before these can go live

Confirmed real by this test run (`pending_forms/JNB_FIELD_MAPPING.md`, the doc this list
originally echoed, no longer exists — `pending_forms/` was fully retired 2026-09-12):
real values for contractor's business address/email, license expiration date, workers' comp
carrier + policy + expiration, and city business license numbers. Plus the Westminster shared-
address-field issue needs a decision (can't be fixed in mapping alone). Per EcoSolar's decision
2026-09-12: workers' comp and the two license-expiration fields are staying unmapped/blank -
no JNB tracking is being added for them, staff fills those by hand on the printed output.
