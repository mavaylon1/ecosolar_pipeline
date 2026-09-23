"""
Fills every form for every city in forms/ using that city's real permit_data.json (from
build_data.py), and writes a verification CSV per form mapping each PDF field back to its
JobNimbus source.

All output (filled PDFs, VERIFY csvs, fill_reports.json) goes to output/ - nothing else
depends on files in there being current, so it's always safe to delete the whole directory
and regenerate it by re-running this script.

Usage: .venv/bin/python src/forms/run_all.py
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from forms.fill import fill_pdf_form, _load
from forms.registry import FORMS_DIR, form_name
from forms.verify import build_rows

ROOT = FORMS_DIR.parent
OUTPUT_DIR = ROOT / "output"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_reports = {}

    for city_dir in sorted(p for p in FORMS_DIR.iterdir() if p.is_dir()):
        city_key = city_dir.name
        data_path = OUTPUT_DIR / city_key / "permit_data.json"
        if not data_path.exists():
            print(f"{city_key:20s} SKIPPED — no permit_data.json yet (run build_data.py first)")
            continue
        data = _load(data_path)

        city_out = OUTPUT_DIR / city_key
        city_out.mkdir(parents=True, exist_ok=True)

        for mapping_path in sorted(city_dir.glob("mapping*.json")):
            mapping = _load(mapping_path)
            template_path = city_dir / mapping["template"]
            name = form_name(mapping_path) or "application"
            key = f"{city_key}/{name}"
            pdf_out = city_out / f"{name}_filled.pdf"
            try:
                report = fill_pdf_form(
                    pdf_path=template_path,
                    data_path=data_path,
                    mapping_path=mapping_path,
                    output_path=pdf_out,
                )
                all_reports[key] = report
                print(f"{key:35s} status={report['status']:14s} "
                      f"filled={len(report['filled_pdf_fields']):3d} issues={len(report['issues'])}")
            except Exception as e:
                all_reports[key] = {"status": "ERROR", "error": str(e)}
                print(f"{key:35s} ERROR: {e}")
                continue

            rows = build_rows(data, mapping_path, template_path)
            csv_path = city_out / f"VERIFY_{name}.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["pdf_field", "schema_key", "jobnimbus_source", "value", "status"])
                writer.writerows(rows)

    reports_path = OUTPUT_DIR / "fill_reports.json"
    reports_path.write_text(json.dumps(all_reports, indent=2))
    print(f"\nAll output written to {OUTPUT_DIR}")

    errored = [k for k, r in all_reports.items() if r.get("status") == "ERROR"]
    if errored:
        print(f"\n{len(errored)} form(s) failed to process entirely: {errored}")


if __name__ == "__main__":
    main()
