# Garden Grove — Solar Permit Application

**Form:** City of Garden Grove Building & Safety Division — Permit Application  
**Template file:** `template.pdf`  
**Mapping file:** `mapping.json`  
**Trigger jurisdiction:** job city = `"Garden Grove"`

---

## PDF Fields and Their Sources

### From JNB Job Record

| PDF Field | JNB Field | Notes |
|---|---|---|
| Job Address | `address_line1`, `city`, `state_text`, `zip` | Joined with commas |
| Residential (checkbox) | `Property Type` | See controlled values below |
| Commercial (checkbox) | `Property Type` | See controlled values below |
| Job Description 1/2/3 | `job_description` | Engineer-entered. Long text wraps across 3 lines. |
| Panel Count (`undefined_4`) | `Number Panels` | |
| System kW (`undefined_5`) | `system_kw_ac` → fallback `System size DC` | AC preferred. Falls back to DC if AC not present. |
| Existing Solar (radio) | `existing_panels` | Engineer-entered. See controlled values below. |
| Main Structure (checkbox) | `structure` | Engineer-entered. Parsed from comma-separated value. |
| Garage (checkbox) | `structure` | Engineer-entered. |
| Patio (checkbox) | `structure` | Engineer-entered. |
| Accessory Structure (checkbox) | `structure` | Engineer-entered. |
| Valuation | Calculated | See calculation below. |

### From JNB Contact Record

The contact is fetched using the `primary` field on the job (a dict with an `id` key).

| PDF Field | JNB Field | Notes |
|---|---|---|
| Property Owner | `first_name` + `last_name` | Falls back to `display_name` if name fields empty. |
| HO Phone (`Phone No` / `undefined`) | `home_phone` → `mobile_phone` → `work_phone` | Uses first non-empty value in that order. Split into area code + rest. |

### Static / Hardcoded

These values never change. Update `transformer.py` if they do.

| PDF Field | Value |
|---|---|
| Contractor | Ecosolar USA Electric LLC |
| Contractor Phone (`Phone No_2` / `undefined_2`) | (714) 265-9077 |
| State License | 1045300 |
| Class | C10, C46 |
| Applicant | Allysa Dizon |
| Applicant Phone (`Phone No_3` / `undefined_3`) | (657) 629-5991 |
| Applicant Address | 13902 Harbor Blvd, Unit 2A, Garden Grove CA 92843 |
| Applicant Email (`Email`) | permit@ecosolarusa.com |
| Electrical (checkbox) | Always checked |
| Solar (checkbox) | Always checked |

### Not Filled (left blank)

| PDF Field | Reason |
|---|---|
| SIGNATURE | Requires physical signature |
| DATE | Filled at time of signing |
| Business Tax | Not required for EcoSolar |
| PLAN CHECK OR PERMIT | Assigned by city at submission |
| ENTITLEMENT NO | Assigned by city |

---

## Calculations

### Valuation

```
valuation = round(kW) × $2,000 + (number of batteries × $2,500)
```

- `kW` comes from `system_kw_ac` (or `System size DC` if AC not present)
- `number of batteries` comes from JNB field `Number of Battery`
- `round()` is standard rounding (0.5 rounds up)
- Result is stored as a plain integer string, e.g. `"6000"`

**Example:** 2.64 kW, 0 batteries → round(2.64) = 3 → 3 × $2,000 = **$6,000**  
**Example:** 7.2 kW, 1 battery → round(7.2) = 7 → 7 × $2,000 + 1 × $2,500 = **$16,500**

---

## Controlled Values

### Property Type → Residential / Commercial

| JNB `Property Type` value | Residential checkbox | Commercial checkbox |
|---|---|---|
| `Single Family` | ✓ | |
| `Townhome` | ✓ | |
| `Commercial Building` | | ✓ |
| (empty) | ✓ (default) | |

Defined in `transformer._COMMERCIAL_TYPES`. Add new commercial types there if needed.

### Structure Checkboxes

`structure` is a comma-separated string entered by the engineer. Each token maps to a checkbox:

| Value in `structure` field | PDF Checkbox |
|---|---|
| `Main` or `Main Structure` | Main Structure |
| `Garage` | Garage |
| `Patio` | Patio |
| `Accessory` or `Accessory Structure` | Accessory Structure |

**Example:** `"Main,Garage"` → Main Structure ✓, Garage ✓, Patio ☐, Accessory Structure ☐

### Existing Solar Panels

`existing_panels` is a yes/no field entered by the engineer. Maps to the radio button:  
`"Yes"` → Yes selected, `"No"` (or missing) → No selected.

---

## Engineer-Entered Fields

These 4 fields were added to JNB on 2026-05-29 and must be filled by the engineer before the pipeline runs:

| JNB Field | Type | Description |
|---|---|---|
| `job_description` | Text | Description of work, written per Alyssa's format from the plan sheet |
| `structure` | Comma-separated | Structures in scope: `Main`, `Garage`, `Patio`, `Accessory Structure` |
| `existing_panels` | Yes/No | Whether solar panels are already installed on the roof |
| `system_kw_ac` | Number | AC system kW from the plan set |

---

## PDF Field Name Reference

Some PDF fields have non-descriptive auto-generated names:

| PDF Field Name | What It Is |
|---|---|
| `undefined_4` | Solar panel count |
| `undefined_5` | System kW |
| `undefined` | HO phone — rest of number (after area code) |
| `undefined_2` | Contractor phone — rest of number |
| `undefined_3` | Applicant phone — rest of number |
| `Phone No` | HO phone — area code only |
| `Phone No_2` | Contractor phone — area code only |
| `Phone No_3` | Applicant phone — area code only |
