import pathlib
import fitz

SRC = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/pending_forms/la_county/LACountyBSDPermitDeclaration.pdf"
OUT_DIR = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/pending_forms_fillable/la_county"

def _r(x0, y0, x1, y1):
    return (x0, y0, x1, y1)

# Fields too narrow for a fixed 9pt font (would clip) - let these auto-shrink instead.
AUTO_FONT_FIELDS = {"License Class", "Workers Comp Phone Number"}

FIELDS = [
    ("Owner Builder Date", _r(66, 221.6, 120, 234.5)),
    ("Owner Builder Signature", _r(303, 221.6, 590, 234.5)),
    ("License Class", _r(94, 264.2, 108, 277.1)),
    ("License Number", _r(158, 264.2, 276, 277.1)),
    ("Contractor Signature", _r(360, 264.2, 590, 277.1)),
    ("Applicant Print Name", _r(122, 326, 260, 338.9)),
    ("Applicant Signature Lobbyist", _r(338, 326, 590, 338.9)),
    ("Company Name", _r(99, 344.3, 389, 357.2)),
    ("Lobbyist Cert Date", _r(416, 344.3, 590, 357.2)),
    ("Workers Comp Carrier", _r(406, 446, 590, 459)),
    ("Workers Comp Policy Number", _r(94, 455.4, 179, 468.3)),
    ("Workers Comp Expiration Date", _r(242, 455.4, 320, 468.3)),
    ("Workers Comp Agent Name", _r(382, 455.4, 470, 468.3)),
    ("Workers Comp Phone Number", _r(531, 455.4, 590, 468.3)),
    ("Signature Of Applicant", _r(120, 492.6, 282, 505.5)),
    ("Signature Of Applicant Date", _r(310, 492.6, 590, 505.5)),
    ("Lenders Name", _r(96, 640.3, 344, 653.2)),
    ("Branch Designation", _r(422, 640.3, 590, 653.2)),
    ("Lenders Address", _r(104, 649.6, 590, 662.5)),
    ("Final Signature Property Owner", _r(216, 737.5, 437, 750.4)),
    ("Final Signature Date", _r(464, 737.5, 590, 750.4)),
]

DUMMY = {
    "Owner Builder Date": "",
    "Owner Builder Signature": "",
    "License Class": "C-10",
    "License Number": "123456",
    "Contractor Signature": "Jane Engineer",
    "Applicant Print Name": "",
    "Applicant Signature Lobbyist": "",
    "Company Name": "EcoSolar USA Electric LLC",
    "Lobbyist Cert Date": "07/28/2026",
    "Workers Comp Carrier": "Sample Insurance Co",
    "Workers Comp Policy Number": "WC-998877",
    "Workers Comp Expiration Date": "12/31/2026",
    "Workers Comp Agent Name": "Sam Agent",
    "Workers Comp Phone Number": "(714) 555-0300",
    "Signature Of Applicant": "Jane Engineer",
    "Signature Of Applicant Date": "07/28/2026",
    "Lenders Name": "N/A",
    "Branch Designation": "",
    "Lenders Address": "",
    "Final Signature Property Owner": "John Homeowner",
    "Final Signature Date": "07/28/2026",
}

doc = fitz.open(SRC)
page = doc[0]
for name, rect in FIELDS:
    w = fitz.Widget()
    w.field_name = name
    w.rect = fitz.Rect(*rect)
    w.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    w.field_value = ""
    w.text_fontsize = 0 if name in AUTO_FONT_FIELDS else 9
    w.border_color = (0, 0.4, 0.8)
    w.border_width = 0.6
    page.add_widget(w)

pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
doc.save(f"{OUT_DIR}/LACountyBSDPermitDeclaration_fillable.pdf")

for page in doc:
    for w in page.widgets() or []:
        if w.field_name not in DUMMY:
            continue
        w.field_value = str(DUMMY[w.field_name])
        w.update()

doc.save(f"{OUT_DIR}/LACountyBSDPermitDeclaration_dummy_filled.pdf")
doc.close()
print("done")
