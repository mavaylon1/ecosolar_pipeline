import pathlib
import fitz

SRC = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/not_possible_forms/anaheim/B701-PERMIT EXTENSION REQUEST FORM_202508282224398561.pdf"
OUT_DIR = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/not_possible_forms/anaheim"

FIELDS = [
    ("Last Name", "text", (33, 161, 181, 179), False),
    ("First Name", "text", (186, 161, 361, 179), False),
    ("Company Name", "text", (366, 161, 579, 179), False),
    ("Mailing Address", "text", (33, 212, 294, 230), False),
    ("City", "text", (299, 212, 451, 230), False),
    ("State", "text", (456, 212, 510, 230), False),
    ("Zip", "text", (515, 212, 579, 230), False),
    ("Area Code Phone Number", "text", (33, 260, 188, 284), False),
    ("Email", "text", (193, 260, 579, 284), False),
    ("Job Location", "text", (118, 322, 565, 341), False),
    ("Permit Numbers", "text", (45, 362, 567, 381), True),
    ("Reason For Extension", "text", (45, 404, 567, 508), True),
    ("Signature", "text", (33, 543, 220, 562), False),
    ("Title Of Claimant", "text", (225, 543, 411, 562), False),
    ("Date", "text", (417, 543, 579, 562), False),
]

DUMMY = {
    "Last Name": "Engineer",
    "First Name": "Jane",
    "Company Name": "EcoSolar USA Electric LLC",
    "Mailing Address": "456 Solar Way",
    "City": "Garden Grove",
    "State": "CA",
    "Zip": "92840",
    "Area Code Phone Number": "(714) 555-0200",
    "Email": "permits@ecosolar.example.com",
    "Job Location": "123 Main St, Anaheim, CA 92805",
    "Permit Numbers": "B715-2026-00123",
    "Reason For Extension": "Additional time needed to complete final utility interconnection inspection.",
    "Signature": "Jane Engineer",
    "Title Of Claimant": "Authorized Agent",
    "Date": "07/28/2026",
}

doc = fitz.open(SRC)
page = doc[0]
for name, kind, rect, multiline in FIELDS:
    w = fitz.Widget()
    w.field_name = name
    w.rect = fitz.Rect(*rect)
    w.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    w.field_value = ""
    if multiline:
        w.field_flags = 4096  # multiline
        w.text_fontsize = 9
    w.border_color = (0, 0.4, 0.8)
    w.border_width = 0.6
    page.add_widget(w)

pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
doc.save(f"{OUT_DIR}/B701_fillable.pdf")

for page in doc:
    for w in page.widgets() or []:
        if w.field_name not in DUMMY:
            continue
        w.field_value = str(DUMMY[w.field_name])
        w.update()

doc.save(f"{OUT_DIR}/B701_dummy_filled.pdf")
doc.close()
print("done")
