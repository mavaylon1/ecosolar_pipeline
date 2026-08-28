# Form field → JobNimbus field mapping (priority cities)

Simple 1:1 reference: for each field on the form, what JobNimbus field fills it, and any note. For
review — does this look right?

---

## Garden Grove — Permit Declaration
`pending_forms/garden_grove/permit-declaration-3-25-20.pdf`

| Form Field | JobNimbus Field | Notes |
|---|---|---|
| PERMIT NO | — | Assigned by city |
| Owner-builder checkbox (2 options) | — | Always check "exclusively contracting with licensed contractors" — EcoSolar is the contractor |
| Signature 1, Date | — | Signed at filing |
| License Class | Static: C10, C46 | |
| State Lic No | Static: 1045300 | |
| Business Tax No | — | Not currently tracked, need value |
| Contractor Name | Static: Ecosolar USA Electric LLC | |
| ContractorAgent 1 | ? | Unclear whose name goes here — need a decision |
| Phone No | Static: (714) 265-9077 | |
| Address | — | Contractor's business address — not currently tracked |
| Policy No 1, Carrier, Expiration Date | — | EcoSolar's workers' comp info — not currently tracked, need real values |
| Signature 1_2/Date_2, Signature/Date_3 | — | Signed at filing |

---

## Fountain Valley — Permit Application
`pending_forms/fountain_valley/Permit Application page 1_201504201306210151.pdf`

| Form Field | JobNimbus Field | Notes |
|---|---|---|
| BUILDING ADDRESS | job: address_line1, city, state_text, zip | |
| UNIT # | job: address_line2 | Was empty on the sample job — confirm it's ever used |
| DESCRIPTION OF WORK (4 lines) | job: Job_description | Wraps across lines |
| REMODEL SQUARE FEET, NEW SQUARE FEET | — | Not applicable to solar |
| VALUATION | Calculated | round(kW)×$2,000 + batteries×$2,500 |
| TYPE OF CONSTRUCTION, OCCUPANCY GROUP, OCCUPANCY LOAD | — | No JNB field — need a fixed default or confirm it varies |
| OWNER NAME | contact: first_name + last_name | |
| PHONE | contact: home_phone → mobile_phone → work_phone | |
| EMAIL ADDRESS | contact: email | |
| OWNER ADDRESS/CITY/STATE/ZIP | contact: address_line1, city, state_text, zip? | Not currently pulled — job's address is used everywhere else instead of the contact's own address. Same address in most cases, but worth confirming |
| APPLICANT NAME | Static: Allysa Dizon | |
| APPLICANT PHONE | Static: (657) 629-5991 | |
| APPLICANT EMAIL/ADDRESS/CITY/STATE/ZIP | Static, but not fully set up | Only have one combined address string today, not split into city/state/zip |
| CONTRACTOR | Static: Ecosolar USA Electric LLC | |
| CONTRACTOR PHONE | Static: (714) 265-9077 | |
| CONTRACTOR EMAIL/ADDRESS/CITY/STATE/ZIP | — | Not currently tracked, need values |
| STATE LICENSE #, LICENSE TYPE | Static: 1045300 / C10, C46 | |
| EXP DATE (license) | — | Not currently tracked |
| WORKERS COMP CARRIER, EXP DATE, POLICY, PHONE | — | Not currently tracked, need real values |
| CITY BUS. LICENSE #, EXP DATE | — | Confirm EcoSolar has one for Fountain Valley |

---

## Huntington Beach — Photovoltaic Solar Permit Application
`pending_forms/huntington_beach/Photovoltaic Solar Permit (Residential Only) Application.pdf`

| Form Field | JobNimbus Field | Notes |
|---|---|---|
| Job Address | job: address_line1, city, state_text, zip | |
| Property Owner's Name | contact: first_name + last_name | |
| Owner Address | contact: address_line1, city, state_text, zip? | Same open question as Fountain Valley |
| Phone Number | contact: home_phone → mobile_phone → work_phone | |
| Email | contact: email | |
| Contractor's State License No | Static: 1045300 | |
| MFD/SFD checkboxes | job: Property Type ("Single Family" → SFD)? | Plausible but need to confirm which 2 of the 4 generic "Check Box" widgets these are |
| Photovoltaic fee qty, Meter Size fee qty, EV Chargers fee qty, Sub-panel fee qty, PV Charge/kw fee qty | — | Fee-schedule boxes, filled by whoever calculates fees, not JNB data |
| Energy Storage System fee qty | job: Number of Battery (>0 → checked)? | Plausible, needs confirming |
| Structural Calculations Yes/No | — | Engineer/staff call |
| Reroof section (slope, layers, roofing material, tear-off, sheathing, underlayment, etc.) | — | Not applicable unless combining solar + reroof |

---

## Huntington Beach — Asbestos / Permit Disclosure Form
`pending_forms/huntington_beach/Permit & Asbestos Disclosure Form.pdf`

| Form Field | JobNimbus Field | Notes |
|---|---|---|
| Project Address (p1) | job: address_line1, city, state_text, zip | |
| Scope of Work | job: Job_description | |
| Applicant Name, Applicant Phone Number | Static: Allysa Dizon / (657) 629-5991 | |
| Owner / Owner-Builder-Hiring-Contractor / Contractor checkbox (3 options) | — | Always check "Contractor" |
| Date, Date_2 (p1) | — | Signed at filing |
| Permit Number, Permit Number_2 | — | Assigned by city |
| Address (p2, field name "Text4") | job: address_line1, city, state_text, zip | Second copy of job address on the bundled page-2 form |
| Signature, Date_3 (p2) | — | Signed at filing |

---

## Westminster — Building Permit Application
`pending_forms/westminster/Building Permit Application.pdf`

| Form Field | JobNimbus Field | Notes |
|---|---|---|
| Bldg Address | job: address_line1, city, state_text, zip | |
| Description of Work (2 fields) | job: Job_description | |
| Valuation | Calculated | Same formula as Garden Grove |
| Owner Name, Phone | contact: first_name + last_name, home_phone → mobile_phone → work_phone | |
| Owner Address/City/State/Zip | contact: address_line1, city, state_text, zip? | Same open question as Fountain Valley |
| Applicant Name/Phone/Address/City/State/Zip | Static, but not fully set up | City/state/zip not currently split out |
| Contractor Name/Phone/Address/City/State/Zip | Static, but not fully set up | No contractor email/address/city/state/zip currently defined |
| State License No, License Type | Static: 1045300 / C10, C46 | |
| Expire Date (license) | — | Not currently tracked |
| Construction, Occupancy, Square Feet | — | No JNB field / not applicable to solar |
| City License No | — | EcoSolar's Westminster business license — not currently tracked |
| Electrical/Mechanical/Plumbing System table (~130 fields) | — | Fee-schedule worksheet, out of scope |
| Planning Reference #, Okay to Submit/Approved checkboxes, By, Date | — | Staff-only |

---

## Westminster — Building Permit Declaration
`pending_forms/westminster/Building Permit Declaration.pdf`

| Form Field | JobNimbus Field | Notes |
|---|---|---|
| Contractor Print Name | Static: Ecosolar USA Electric LLC | |
| License Class and No | Static: C10, C46 + 1045300 | |
| Expiration Date (license) | — | Not currently tracked |
| WC declaration checkbox (3 options) | — | Always check "maintain workers' compensation insurance" |
| Carrier, Policy Number | — | EcoSolar's real WC info not currently tracked — needed to actually fill this truthfully |
| Applicant Print Name (appears twice) | Static: Allysa Dizon | Same value both times |
| Owner-builder declaration checkbox (2 options) | — | Always "exclusively contracting with licensed contractors" — signed by the property owner, not EcoSolar |
| "licensed pursuant to..." checkbox | — | Always checked — EcoSolar is licensed |
| Section Exempt, Reason Exempt | — | Not applicable — not claiming a licensing exemption |
| Owner Print Name | contact: first_name + last_name | |
| Signature of Applicant, Date | — | Signed at filing |
