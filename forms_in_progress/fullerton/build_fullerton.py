import pathlib
import fitz

SRC = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/forms_in_progress/fullerton/SolarPermitApplication98.pdf"
OUT_DIR = "/Users/matchu/Research/ecosolar/ecosolar_pipeline/forms_in_progress/fullerton"

FIELDS = [
    ("Project Address", (119, 84.3, 333, 98.3), False),
    ("Suite", (367, 84.3, 433, 98.3), False),
    ("Tidemark Number", (485, 83.4, 590, 99.4), False),
    ("Master ID Number", (494, 118.8, 590, 132.8), False),
    ("Job Description", (30, 181, 590, 278), True),
    ("Number Of Panels", (167, 280.4, 360, 296.9), False),
    ("System kWAC", (431, 278.7, 590, 295.3), False),
    ("Building Owner Name", (147, 314.5, 412, 328.6), False),
    ("Owner Phone", (474, 314.5, 588, 328.6), False),
    ("Owner Address", (76, 344.5, 283, 358.6), False),
    ("Owner City", (314, 344.5, 416, 358.6), False),
    ("Owner State", (455, 344.5, 506, 358.6), False),
    ("Owner Zip", (530, 344.5, 590, 358.6), False),
    ("Tenant Name", (153, 376.3, 416, 390.4), False),
    ("Tenant Phone", (474, 376.3, 590, 390.4), False),
    ("Contractor Name", (131, 408.1, 278, 422.2), False),
    ("Contractor State Contr Number", (366, 408.1, 411, 422.2), False),
    ("Contractor License Class", (492, 408.1, 501, 422.2), False),
    ("Contractor Phone", (563, 408.1, 590, 422.2), False),
    ("Contractor Address", (76, 438.1, 278, 452.2), False),
    ("Contractor City", (314, 438.1, 411, 452.2), False),
    ("Contractor State", (455, 438.1, 500, 452.2), False),
    ("Contractor Zip", (530, 438.1, 590, 452.2), False),
    ("Workers Comp Policy Number", (150, 469.6, 169, 483.7), False),
    ("Workers Comp Exp Date", (231, 469.6, 278, 483.7), False),
    ("Insurance Company", (393, 469.6, 411, 483.7), False),
    ("Fullerton Business License Number", (528, 469.6, 590, 483.7), False),
    ("Architect Engineer Name", (132, 501.4, 283, 515.5), False),
    ("Architect State License Number", (370, 501.4, 416, 515.5), False),
    ("Architect Phone", (474, 501.4, 590, 515.5), False),
    ("Contact Name", (105, 563.2, 328, 577.2), False),
    ("Contact Phone", (387, 563.2, 590, 577.2), False),
    ("Email Address", (109, 584.4, 590, 598.4), False),
    ("Fire Class", (86, 614.8, 411, 632.1), False),
    ("Bldg Fee", (467, 618.1, 590, 632.2), False),
    ("Occ Group", (84, 644.2, 411, 658.2), False),
    ("PC Fee Paid", (470, 644.2, 590, 658.2), False),
    ("Type Of Constr", (105, 667.9, 211, 681.9), False),
    ("Valuation", (272, 670.1, 411, 684.2), False),
    ("Submittal Date", (499, 670.1, 590, 684.2), False),
    ("Flood Zone", (279, 692.1, 411, 706.1), False),
    ("Processed", (476, 692.1, 590, 706.1), False),
]

DUMMY = {
    "Project Address": "123 Main St, Fullerton, CA 92831",
    "Suite": "",
    "Tidemark Number": "TM-2026-0456",
    "Master ID Number": "M-778899",
    "Job Description": "Install roof-mounted solar PV system with 20 modules and associated electrical equipment.",
    "Number Of Panels": "20",
    "System kWAC": "7.2",
    "Building Owner Name": "John Homeowner",
    "Owner Phone": "(714) 555-0100",
    "Owner Address": "123 Main St",
    "Owner City": "Fullerton",
    "Owner State": "CA",
    "Owner Zip": "92831",
    "Tenant Name": "",
    "Tenant Phone": "",
    "Contractor Name": "EcoSolar USA Electric LLC",
    "Contractor State Contr Number": "123456",
    "Contractor License Class": "C-10",
    "Contractor Phone": "(714) 555-0200",
    "Contractor Address": "456 Solar Way",
    "Contractor City": "Garden Grove",
    "Contractor State": "CA",
    "Contractor Zip": "92840",
    "Workers Comp Policy Number": "WC-998877",
    "Workers Comp Exp Date": "12/31/26",
    "Insurance Company": "Sample Ins Co",
    "Fullerton Business License Number": "FBL-5544",
    "Architect Engineer Name": "N/A",
    "Architect State License Number": "N/A",
    "Architect Phone": "",
    "Contact Name": "Jane Engineer",
    "Contact Phone": "(714) 555-0200",
    "Email Address": "permits@ecosolar.example.com",
    "Fire Class": "",
    "Bldg Fee": "",
    "Occ Group": "",
    "PC Fee Paid": "",
    "Type Of Constr": "",
    "Valuation": "14,000",
    "Submittal Date": "07/28/2026",
    "Flood Zone": "",
    "Processed": "",
}

doc = fitz.open(SRC)
page = doc[0]
for name, rect, multiline in FIELDS:
    w = fitz.Widget()
    w.field_name = name
    w.rect = fitz.Rect(*rect)
    w.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    w.field_value = ""
    if multiline:
        w.field_flags = 4096
        w.text_fontsize = 9
    w.border_color = (0, 0.4, 0.8)
    w.border_width = 0.6
    page.add_widget(w)

pathlib.Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
doc.save(f"{OUT_DIR}/SolarPermitApplication_fillable.pdf")

for page in doc:
    for w in page.widgets() or []:
        if w.field_name not in DUMMY:
            continue
        w.field_value = str(DUMMY[w.field_name])
        w.update()

doc.save(f"{OUT_DIR}/SolarPermitApplication_dummy_filled.pdf")
doc.close()
print("done")
