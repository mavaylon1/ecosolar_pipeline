"""
Westminster Building Permit Application ships with a bug: the "Address" box under
Owner/Applicant/Contractor all share the literal field name "Address" (every other
field on those same rows - Phone/City/State/Zip - correctly got _2/_3 suffixes).
This splits the Applicant and Contractor boxes into their own fields (Address_2,
Address_3) so each can carry its own value, matching the naming pattern already
used elsewhere on this form. Owner's box keeps the original "Address" name.
"""
import fitz

SRC = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/forms_in_progress/westminster/Building Permit Application.pdf"
OUT = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/forms_in_progress/westminster/Building Permit Application_fixed.pdf"

# (y0 to identify which widget, new field name)
RENAMES = {
    248.8: "Address_2",  # Applicant
    289.6: "Address_3",  # Contractor
}

doc = fitz.open(SRC)
page = doc[0]

targets = []
for w in page.widgets() or []:
    if w.field_name == "Address" and round(w.rect.y0, 1) in RENAMES:
        targets.append((w, RENAMES[round(w.rect.y0, 1)]))

assert len(targets) == 2, f"expected 2 widgets to rename, found {len(targets)}"

for widget, new_name in targets:
    rect = widget.rect
    page.delete_widget(widget)
    new_widget = fitz.Widget()
    new_widget.field_name = new_name
    new_widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    new_widget.rect = rect
    new_widget.field_value = ""
    new_widget.text_font = "Helv"
    new_widget.text_fontsize = 0
    page.add_widget(new_widget)

doc.save(OUT)
doc.close()

# Verify
check = fitz.open(OUT)
names = sorted(w.field_name for w in check[0].widgets() or [] if "Address" in w.field_name)
print("Address-related fields now:", names)
check.close()
print(f"Saved {OUT}")
