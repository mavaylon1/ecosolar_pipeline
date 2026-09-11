import pathlib
import fitz

SRC = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/forms_in_progress/anaheim/B715-BUILDING PERMIT APPLICATION_202508282216519191.pdf"
OUT_DIR = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/forms_in_progress/anaheim"

# All rects hand-verified against exact label bboxes from page.search_for() - no auto-detection.
FIELDS = [
    ("Date", "text", (465, 137.7, 601, 158.3)),
    ("Project Address", "text", (135, 155.3, 601, 176)),
    ("Describe Work", "text", (190, 173, 601, 193.6)),
    ("Related Permit Number", "text", (356, 190.6, 601, 211.3)),
    ("Valuation", "text", (111, 208.3, 445, 228.9)),
    ("Print Your Name", "text", (136, 229.5, 279, 250.1)),
    ("Applicant Is Property Owner", "checkbox", (48.1, 262.4, 58.8, 275.8)),
    ("Applicant Is Contractor", "checkbox", (48.1, 277.1, 58.8, 290.4)),
    ("Employee Of Owner", "checkbox", (99.4, 306.4, 110.1, 319.7)),
    ("Employee Of Contractor", "checkbox", (154.0, 306.4, 164.7, 319.7)),
    ("Property Owner Name", "text", (348, 258.9, 558, 279)),
    ("Property Owner Address", "text", (358, 276.6, 558, 296.6)),
    ("Property Owner Phone", "text", (393, 294.2, 558, 314.3)),
    ("Property Owner Email", "text", (349, 311.8, 558, 331.9)),
    ("Contractor Company Name", "text", (87, 377.2, 279, 397.3)),
    ("Contractor Address", "text", (79, 394.9, 279, 414.9)),
    ("Contractor City", "text", (58, 412.5, 279, 432.6)),
    ("Contractor Phone", "text", (114, 430.2, 279, 450.2)),
    ("Contractor State License", "text", (466, 375.4, 558, 395.5)),
    ("Contractor City License", "text", (384, 393.1, 558, 413.1)),
    ("Contractor State Zip", "text", (364, 413.7, 558, 433.8)),
    ("Contractor Email", "text", (349, 434.4, 558, 454.4)),
    ("Workers Comp Policy Carrier", "text", (104, 495.3, 279, 515.4)),
    ("Workers Comp Expiration Date", "text", (115, 513, 279, 533)),
    ("Workers Comp Agent Name", "text", (100, 530.6, 279, 550.7)),
    ("Workers Comp Policy Number", "text", (356, 493.5, 558, 513.6)),
    ("Workers Comp Agent Phone", "text", (424, 525.9, 558, 546)),
    ("Workers Comp Exempt", "checkbox", (56.1, 554.3, 62.8, 562.65)),
]

DUMMY = {
    "Date": "07/28/2026",
    "Project Address": "123 Main St, Anaheim, CA 92805",
    "Describe Work": "Install roof-mounted solar PV system, 20 modules",
    "Related Permit Number": "N/A",
    "Valuation": "14,000",
    "Print Your Name": "Jane Engineer",
    "Applicant Is Property Owner": False,
    "Applicant Is Contractor": True,
    "Employee Of Owner": False,
    "Employee Of Contractor": True,
    "Property Owner Name": "John Homeowner",
    "Property Owner Address": "123 Main St, Anaheim, CA 92805",
    "Property Owner Phone": "(714) 555-0100",
    "Property Owner Email": "john@example.com",
    "Contractor Company Name": "EcoSolar USA Electric LLC",
    "Contractor Address": "456 Solar Way",
    "Contractor City": "Garden Grove",
    "Contractor Phone": "(714) 555-0200",
    "Contractor State License": "123456",
    "Contractor City License": "CL-7890",
    "Contractor State Zip": "CA, 92840",
    "Contractor Email": "permits@ecosolar.example.com",
    "Workers Comp Policy Carrier": "Sample Insurance Co",
    "Workers Comp Expiration Date": "12/31/2026",
    "Workers Comp Agent Name": "Sam Agent",
    "Workers Comp Policy Number": "WC-998877",
    "Workers Comp Agent Phone": "(714) 555-0300",
    "Workers Comp Exempt": False,
}

doc = fitz.open(SRC)
page = doc[0]
for name, kind, rect in FIELDS:
    w = fitz.Widget()
    w.field_name = name
    w.rect = fitz.Rect(*rect)
    if kind == "checkbox":
        w.field_type = fitz.PDF_WIDGET_TYPE_CHECKBOX
        w.field_value = False
    else:
        w.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        w.field_value = ""
    w.border_color = (0, 0.4, 0.8)
    w.border_width = 0.6
    page.add_widget(w)

pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
doc.save(f"{OUT_DIR}/B715_fillable.pdf")

for page in doc:
    for w in page.widgets() or []:
        if w.field_name not in DUMMY:
            continue
        val = DUMMY[w.field_name]
        if w.field_type_string == "CheckBox":
            w.field_value = bool(val)
        else:
            w.field_value = str(val)
        w.update()

doc.save(f"{OUT_DIR}/B715_dummy_filled.pdf")
doc.close()
print("done")
