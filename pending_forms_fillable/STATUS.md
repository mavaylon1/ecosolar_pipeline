# Pending forms → fillable conversion — status

## Goal
Some city permit PDFs in `pending_forms/` are flat (no AcroForm fields) but have a
real text layer. Rather than build a generic reusable converter, we're hand-digitizing
each one directly: find each label's exact position via `page.search_for(...)`, place a
`fitz.Widget` text/checkbox field next to it at hand-verified coordinates, then fill
with dummy data and render to PNG for visual QA. No reusable tool is being built —
this is a one-time job per form (see conversation: "I don't really care if we have a
tool that works for converting all forms... I don't plan on having to convert more forms").

This directory also holds forms that turned out to **already be fillable natively** — no
hand-conversion needed, just moved here (2026-09-11) so every "ready for a mapping to be
written" form lives in one place, regardless of whether it needed conversion work first.
Those are marked "already fillable, no conversion done" in the table below - don't assume
every file here went through the hand-digitizing process.

**Where a form's files live changes as it progresses** (folder taxonomy, 2026-09-11):
`pending_forms/` = not fillable yet, but possible, not started. `pending_forms_fillable/`
(here) = fillable (native or hand-converted) but no mapping/testing started yet.
`forms_in_progress/` = has a mapping and is being tested or has been tested against real JNB
data — this is where a form's files move to once work starts on it, so don't expect Anaheim
B715/Fullerton/LA County's files to stay here once they're done (see their table rows).
`forms/` = tested and live in production. `not_possible_forms/` = structurally blocked.

Scope note: only the **applicant-facing** fields are being digitized. City-staff-only
sections (fee schedules, "Department Action" approval blocks, plan-check routing boxes)
are intentionally skipped. Big non-solar checklist tables (e.g. Anaheim B715 page 2's
room-addition/reroof/patio grid) are also skipped — not relevant to EcoSolar's solar
permit use case.

## Tools/method used
- PyMuPDF (`fitz`), via the repo's `.venv` (`.venv/bin/python`).
- `page.search_for("exact label text")` to get each label's precise bbox (case-insensitive,
  so watch for substring collisions — e.g. "Name:" matches inside "PRINT YOUR NAME:" too;
  check `hits` list length and pick the right occurrence, or better, search a more specific
  string).
- `page.get_drawings()` filtered to thin rects (`height <= 1.6, width >= 10`) to find real
  cell/column divider lines — **do not** guess column widths from label positions alone,
  always pull actual divider x-coordinates for any bordered table row (see "lessons learned").
- `fitz.Widget()` with `field_type = fitz.PDF_WIDGET_TYPE_TEXT` or `_CHECKBOX`, placed via
  `page.add_widget(w)`.
- Render checks: `page.get_pixmap(dpi=150).save(...)` on the dummy-filled output, viewed via
  the Read tool, after every change. For close-up checks on suspected overlap, render a
  cropped region at `dpi=300-400` (`get_pixmap(dpi=400, clip=fitz.Rect(...))`).

## Lessons learned (read before continuing)
1. **Always fetch real divider coordinates for table-style rows.** Guessing a field's right
   edge from "where the next label starts" caused fields to overlap adjacent cell borders
   (caught by user on the Fullerton contractor-info row). Query
   `page.get_drawings()` for thin vertical rects (`width < 2, height > 5`) within the row's
   y-band first.
2. **Auto font size (`text_fontsize = 0`) sits text close to/on the printed underline** in
   tightly-fit boxes — looks like a bug but often isn't (compare to the printed label's own
   baseline, which touches the same line by design in many of these forms). A fixed
   `text_fontsize = 9` usually gives cleaner clearance above the line, BUT clips text in
   narrow boxes (e.g. "C-10" in a 14pt-wide License Class box, or a full phone number in a
   59pt box). Fix: use fixed 9pt as default, keep an explicit override list
   (`AUTO_FONT_FIELDS` set in `build_lacounty.py`) for fields too narrow for it, and check
   both narrow and wide fields after any font-size change.
3. **Don't apply a blanket vertical shift to fix one bad field.** A global 5pt shift-up
   applied to fix LA County's "Lender's Name" (whose box was too tall and bottom-heavy)
   ended up pushing *other* fields up into the paragraph line above them, since row spacing
   isn't uniform across the page. Fix problems per-field via crops, not with global offsets.
4. **"Circle one" style selections should NOT get a text field.** Fullerton's "Use of
   Building" (Residential/Commercial/Industrial/Other) and "Nature of Work" (Solar P.V.
   System/Solar Water Heating/Other) rows are meant to be circled by hand, not typed —
   user asked to delete the two boxes that had been added there. Don't add a fill-in field
   for any similar "circle one" pattern in remaining forms.
5. Multiline fields need `w.field_flags = 4096` and should also get an explicit
   `w.text_fontsize` (e.g. 9) — otherwise auto-size picks something huge that strikes
   through the form's ruled lines.

## Status per form

| City | File | Status |
|---|---|---|
| Anaheim | B715 (Building Permit App) | ✅ Done — page 1 only (page 2's room-addition/reroof/patio grid skipped as not solar-relevant). Verified clean render. **Moved to `forms_in_progress/anaheim/` (2026-09-11)** along with its build script and raw source — tested against real JNB data, see `forms_in_progress/registry.py`. |
| Anaheim | B701 (Permit Extension) | ⬅️ **Moved to `not_possible_forms/anaheim/`** (2026-09-11) — see `not_possible_forms/README.md` for why (needs a permit number and extension reason that don't exist in JNB). Widget placement itself was done and verified clean. |
| Anaheim | B705 (Electrical Permit) | ❌ **Not started**, still flat, lives in `pending_forms/anaheim/`. Page 1 mirrors B715's layout (Date/Project Address/Describe Work/Permit#/Print Name+checkboxes/Property Owner box/Contractor box/Workers Comp box) — very similar field set to B715, should go fast reusing that pattern. Page 2 is a fee-schedule quantity table (Meter/Switch Gear, Sub Panels, Fixtures, Motors, PV Inverters/ESS Battery/EV Charger rows) — skip, it's for city fee calc, not applicant data. |
| Fullerton | Solar Permit Application Worksheet | ✅ Done — applicant-facing fields only. Verified clean render, no overlap with any printed line/box (re-confirmed 2026-08-28 via 400dpi close-up). **Moved to `forms_in_progress/fullerton/` (2026-09-11)** along with its build script and raw source — tested against real JNB data. **Known issue:** Workers Comp Policy#, Insurance Company, and Contractor Phone sit in very narrow boxes and need forced tiny font sizes to fit — not overlapping anything, but hard to read (Contractor Phone worst at 3.5pt). License Class (9pt box) is mathematically too narrow for any text and was left unmapped entirely. Candidate for the later spacing-fixes pass, same bucket as the text-overflow work tracked in `TODO.md`. |
| Corona | Building Plan Check App | ❌ **Not started**, still flat, lives in `pending_forms/corona/`. Scope agreed: header/applicant fields (Project Address, Tract#, Lot#, Name/Phone/Email, Address, City/Zip, Owner Email/Phone, Construction Type, Occupancy Type) + the two Photovoltaic kW in DC / kW in AC line items from the big Electrical checklist column. Skip the rest of the huge Building/Plumbing/Electrical/Mechanical checklist grid. |
| Pomona | Plan Check/Permit App | ❌ **Not started**, still flat, lives in `pending_forms/pomona/`. Scope agreed: header/applicant fields (Project Address, Project Owner, Contractor/Engineer/Architect, addresses, phones, emails, Contact, Description of Work, Commercial/Residential checkbox pair, the 4 Yes/No checkboxes) + the "SOLAR PANELS" sub-section (Kilowatts, # of Panels, Panel Upgrade amps, # of Branch Circuits/Breakers, Valuation). Skip the rest of the Building/Electrical/Mechanical/Plumbing checklist grid. |
| LA County | Owner-Builder/Permit Declaration | ✅ **Done — QA complete (2026-08-28).** All 20 fields placed and dummy-filled; re-rendered at 150dpi then crop+zoomed at 400dpi on every field row individually. None show text or box overlap with a printed line or adjacent box. One minor cosmetic note: the Workers Comp Expiration Date value runs up against a leftover `/` character from the original form's day/month/year blank format — not an overlap, just slightly cluttered. **Moved to `forms_in_progress/la_county/` (2026-09-11)** along with its build script and raw source — now filled with real JNB data (a Rowland Heights job; "Los Angeles County" isn't a real JNB city value, see `ROADMAP.md` Phase 3). Mapping intentionally only covers the Licensed Contractor's + Workers' Comp Declaration sections — Owner-Builder Declaration and Lobbyist Ordinance Certification are unmapped, same reasoning as Westminster's declaration. |
| Orange | Photovoltaic Permit Application | ⬅️ **Moved to `not_possible_forms/orange/`** (2026-09-11) — scanned image, no text layer at all. See `not_possible_forms/README.md`. |
| Orange | Express Checklist for Residential Solar PV and ESS System | 🟡 **Already fillable, no conversion needed** (168 fields). Not yet mapped. This is a *different* Orange PDF from the scanned one above — don't confuse the two. |
| Irvine | Minor Residential/OTC Application Package | 🟡 **Already fillable, no conversion needed** (194 fields). Not yet mapped. |
| Kern County | Building Permit Application | 🟡 **Already fillable, no conversion needed** (86 fields). Not yet mapped. |
| Long Beach | app-011 | 🟡 **Already fillable, no conversion needed** (162 fields). Not yet mapped. |
| Long Beach | app-012 | 🟡 **Already fillable, no conversion needed** (127 fields). Not yet mapped. |
| Redlands | Building Permit Application | 🟡 **Already fillable, no conversion needed** (111 fields). Not yet mapped. |
| San Diego County | pds291 | 🟡 **Already fillable, no conversion needed** (122 fields). Not yet mapped. |
| Stanton | Permit Application | 🟡 **Already fillable, no conversion needed** (36 fields). Not yet mapped. |
| Yorba Linda | Building Submittal Form | 🟡 **Already fillable, no conversion needed** (51 fields). Not yet mapped. |

## Files in this directory

Nothing hand-converted lives here anymore — once a hand-converted form gets a mapping and is
tested, its fillable PDF, dummy-filled QA render, build script, and raw source all move together
into `forms_in_progress/<city>/` (see Anaheim B715, Fullerton, and LA County's rows above for
where they went). This directory now only holds forms with no mapping/testing started yet:

**Already fillable, moved here as-is (2026-09-11), no conversion work done on them:**
- `irvine/MinorResidentialOTC_fillable.pdf`
- `kern_county/BuildingPermitApplication_fillable.pdf`
- `long_beach/app-011_fillable.pdf`, `long_beach/app-012_fillable.pdf`
- `redlands/BuildingPermitApplication_fillable.pdf`
- `san_diego_county/pds291_fillable.pdf`
- `stanton/PermitApplication_fillable.pdf`
- `yorba_linda/BuildingSubmittalForm_fillable.pdf`
- `orange/ExpressChecklist_fillable.pdf`

## Next steps (in order)

**Fastest path — already fillable, just needs a mapping.json written and tested against real
JNB data** (same process as Fountain Valley, no PDF work required): Irvine, Kern County, Long
Beach (2 forms), Redlands, San Diego County, Stanton, Yorba Linda, Orange (checklist form).

**Needs hand-conversion first, then a mapping:**
1. Anaheim B705 (reuse B715's approach/coordinates where the layout matches).
2. Corona (scoped fields only).
3. Pomona (scoped fields only).

Once any of these are approved, the real `mapping.json` + `forms/<city>/` registry wiring
(like Garden Grove) is a separate follow-on task — not started, out of scope for this pass.

LA County QA is complete (see table above). Fullerton's narrow-field legibility issue and the
known text-overflow issue tracked in `forms_in_progress`/`TODO.md` are both deferred to a later
spacing-fixes pass, not blocking further form onboarding.
