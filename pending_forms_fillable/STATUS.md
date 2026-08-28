# Pending forms → fillable conversion — status

## Goal
Some city permit PDFs in `pending_forms/` are flat (no AcroForm fields) but have a
real text layer. Rather than build a generic reusable converter, we're hand-digitizing
each one directly: find each label's exact position via `page.search_for(...)`, place a
`fitz.Widget` text/checkbox field next to it at hand-verified coordinates, then fill
with dummy data and render to PNG for visual QA. No reusable tool is being built —
this is a one-time job per form (see conversation: "I don't really care if we have a
tool that works for converting all forms... I don't plan on having to convert more forms").

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
| Anaheim | B715 (Building Permit App) | ✅ Done — page 1 only (page 2's room-addition/reroof/patio grid skipped as not solar-relevant). Verified clean render. **Wired into `forms_in_progress/anaheim/` (2026-08-28)** with real JNB data — see `forms_in_progress/registry.py`. |
| Anaheim | B701 (Permit Extension) | ⬅️ **Moved to `pending_forms/anaheim/`** (2026-08-28) — widget placement was done and verified clean, but this form doesn't fit the JNB-driven pipeline: it requests an extension on an *already-issued* permit, and 2 of its real fields (List all Permit Numbers, State Reason for Requesting an Extension) have no JobNimbus data source at all — the permit number doesn't exist until the city approves the original filing, and the extension reason is written per-request, situationally, long after job creation. Fundamentally a different kind of event than what this pipeline handles today, not a mapping problem to solve. `B701_fillable.pdf`, `B701_dummy_filled.pdf`, and its build script live in `pending_forms/anaheim/` now, kept for whenever there's a decision on how (or whether) to source that data. |
| Anaheim | B705 (Electrical Permit) | ❌ **Not started.** Page 1 mirrors B715's layout (Date/Project Address/Describe Work/Permit#/Print Name+checkboxes/Property Owner box/Contractor box/Workers Comp box) — very similar field set to B715, should go fast reusing that pattern. Page 2 is a fee-schedule quantity table (Meter/Switch Gear, Sub Panels, Fixtures, Motors, PV Inverters/ESS Battery/EV Charger rows) — skip, it's for city fee calc, not applicant data. |
| Fullerton | Solar Permit Application Worksheet | ✅ Done — applicant-facing fields only. Verified clean render, no overlap with any printed line/box (re-confirmed 2026-08-28 via 400dpi close-up). **Wired into `forms_in_progress/fullerton/` (2026-08-28)** with real JNB data. **Known issue:** Workers Comp Policy#, Insurance Company, and Contractor Phone sit in very narrow boxes and need forced tiny font sizes to fit — not overlapping anything, but hard to read (Contractor Phone worst at 3.5pt). License Class (9pt box) is mathematically too narrow for any text and was left unmapped entirely. Candidate for the later spacing-fixes pass, same bucket as the text-overflow work tracked in `TODO.md`. |
| Corona | Building Plan Check App | ❌ **Not started.** Scope agreed: header/applicant fields (Project Address, Tract#, Lot#, Name/Phone/Email, Address, City/Zip, Owner Email/Phone, Construction Type, Occupancy Type) + the two Photovoltaic kW in DC / kW in AC line items from the big Electrical checklist column. Skip the rest of the huge Building/Plumbing/Electrical/Mechanical checklist grid. |
| Pomona | Plan Check/Permit App | ❌ **Not started.** Scope agreed: header/applicant fields (Project Address, Project Owner, Contractor/Engineer/Architect, addresses, phones, emails, Contact, Description of Work, Commercial/Residential checkbox pair, the 4 Yes/No checkboxes) + the "SOLAR PANELS" sub-section (Kilowatts, # of Panels, Panel Upgrade amps, # of Branch Circuits/Breakers, Valuation). Skip the rest of the Building/Electrical/Mechanical/Plumbing checklist grid. |
| LA County | Owner-Builder/Permit Declaration | ✅ **Done — QA complete (2026-08-28).** All 20 fields placed and dummy-filled; re-rendered at 150dpi then crop+zoomed at 400dpi on every field row individually, per the "next step" below. None show text or box overlap with a printed line or adjacent box — whatever the font-size fix left unresolved appears to have since been cleaned up. One minor cosmetic note: the Workers Comp Expiration Date value runs up against a leftover `/` character from the original form's day/month/year blank format — not an overlap, just slightly cluttered. **Mapping written in `forms_in_progress/la_county/` (2026-08-28)** but not yet filled with real data — no JNB job matched city="Los Angeles County" (it's unincorporated territory; jobs there would be filed under an actual community name, unknown). Mapping intentionally only covers the Licensed Contractor's + Workers' Comp Declaration sections — Owner-Builder Declaration and Lobbyist Ordinance Certification are unmapped for the same reason as Westminster's declaration. |
| Orange | Photovoltaic Permit Application | Not in scope — this one is a scanned image with no text layer at all, explicitly called out earlier as the hard case. Not part of this "simple forms" batch. |

## Files in this directory
- `anaheim/B715_fillable.pdf`, `anaheim/B715_dummy_filled.pdf`
  (B701's equivalents moved to `pending_forms/anaheim/` — see table above)
- `fullerton/SolarPermitApplication_fillable.pdf`, `fullerton/SolarPermitApplication_dummy_filled.pdf`
- `la_county/LACountyBSDPermitDeclaration_fillable.pdf`, `la_county/LACountyBSDPermitDeclaration_dummy_filled.pdf`
- `_build_scripts/` — the actual Python scripts used to generate each of the above (rerun with
  `.venv/bin/python pending_forms_fillable/_build_scripts/build_<name>.py` from the repo root).
  Each script hardcodes exact field rects (hand-verified via `search_for`/`get_drawings`, not
  auto-detected) plus a `DUMMY` dict of sample values. Edit rects/dummy values directly and
  rerun to regenerate.

## Next steps (in order)
1. Anaheim B705 (reuse B715's approach/coordinates where the layout matches).
2. Corona (scoped fields only).
3. Pomona (scoped fields only).
4. Once all forms are approved, the real `mapping.json` + `forms/<city>/` registry wiring
   (like Garden Grove) is a separate follow-on task — not started, out of scope for this pass.

LA County QA is complete (see table above). Fullerton's narrow-field legibility issue and the
known text-overflow issue tracked in `forms_in_progress`/`TODO.md` are both deferred to a later
spacing-fixes pass, not blocking further form onboarding.
