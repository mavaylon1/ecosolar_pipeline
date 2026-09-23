# Flat-PDF hand-conversion reference

`pending_forms_fillable/` and `forms_in_progress/` (the staging area this content briefly passed
through) have both been fully retired — every city that passed through them has since moved
straight into `forms/` (mapped and tested) or `ask_ecosolar/` (blocked on an EcoSolar decision).
See `src/forms/registry.py` and `ask_ecosolar/README.md` for current status. This file is kept
as a **technique reference** for the next time a city's source PDF turns out to be flat (no
AcroForm fields) and needs hand-conversion before it can be mapped.

## Method

Flat PDFs with a real text layer get hand-digitized, not run through a generic converter (there
isn't one, and none is planned — this is a one-time job per form, not a reusable tool):
find each label's exact position via `page.search_for(...)`, place a `fitz.Widget` text/checkbox
field next to it at hand-verified coordinates, then fill with dummy data and render to PNG for
visual QA.

Scope note: only **applicant-facing** fields get digitized. City-staff-only sections (fee
schedules, "Department Action" approval blocks, plan-check routing boxes) and big non-solar
checklist tables (e.g. room-addition/reroof/patio grids) are intentionally skipped.

**Tools:**
- PyMuPDF (`fitz`), via the repo's `.venv` (`.venv/bin/python`).
- `page.search_for("exact label text")` for each label's precise bbox (case-insensitive, so watch
  for substring collisions — e.g. "Name:" matches inside "PRINT YOUR NAME:" too; check the `hits`
  list length and pick the right occurrence, or search a more specific string).
- `page.get_drawings()` filtered to thin rects (`height <= 1.6, width >= 10`) to find real
  cell/column divider lines — **do not** guess column widths from label positions alone, always
  pull actual divider x-coordinates for any bordered table row.
- `fitz.Widget()` with `field_type = fitz.PDF_WIDGET_TYPE_TEXT` or `_CHECKBOX`, placed via
  `page.add_widget(w)`.
- Render checks: `page.get_pixmap(dpi=150).save(...)` on the dummy-filled output, viewed after
  every change. For close-up checks on suspected overlap, render a cropped region at
  `dpi=300-400` (`get_pixmap(dpi=400, clip=fitz.Rect(...))`).

## Lessons learned (read before hand-converting another form)

1. **Always fetch real divider coordinates for table-style rows.** Guessing a field's right edge
   from "where the next label starts" caused fields to overlap adjacent cell borders. Query
   `page.get_drawings()` for thin vertical rects (`width < 2, height > 5`) within the row's
   y-band first.
2. **Auto font size (`text_fontsize = 0`) sits text close to/on the printed underline** in
   tightly-fit boxes — looks like a bug but often isn't (the printed label's own baseline often
   touches the same line by design). A fixed `text_fontsize = 9` usually gives cleaner clearance,
   BUT clips text in narrow boxes (e.g. "C-10" in a 14pt-wide License Class box, or a full phone
   number in a 59pt box). Use fixed 9pt as default, keep an explicit override list for fields too
   narrow for it, and check both narrow and wide fields after any font-size change.
3. **Don't apply a blanket vertical shift to fix one bad field.** Row spacing isn't uniform across
   a page — a global offset to fix one bad field can push others into the line above them. Fix
   problems per-field via crops, not with global offsets.
4. **"Circle one" style selections should NOT get a text field.** Some forms print options meant
   to be circled by hand (e.g. "Use of Building: Residential/Commercial/Industrial/Other"), not
   typed into a box — don't add a fill-in field for that pattern.
5. Multiline fields need `w.field_flags = 4096` and an explicit `w.text_fontsize` (e.g. 9) —
   otherwise auto-size picks something huge that strikes through the form's ruled lines.
6. **Some forms draw blank lines as literal underscore text, not vector rects** — `get_drawings()`
   finds nothing for these, even though the same "always get real coordinates, don't guess" rule
   still applies. Use `page.get_text("words")` filtered to tokens containing `_` instead, to get
   the real blank extent.
7. **Double-check the label's *full* extent, not a substring match, before placing the field after
   it.** A field placed after just a substring hit (e.g. "Contractor" instead of the full
   "Contractor/Engineer/Architect/Other:" label) can render on top of the label's tail. Always
   visually verify every field, not just the ones that seem risky.
