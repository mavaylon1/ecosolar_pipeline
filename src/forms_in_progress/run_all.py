"""
Fills every (city, form) pair in registry.py using that city's real permit_data.json, and
writes a verification CSV per form mapping each PDF field back to its JobNimbus source.

All output (filled PDFs, VERIFY csvs, fill_reports.json) goes to forms_in_progress/output/ -
nothing else depends on files in there being current, so it's always safe to delete the
whole directory and regenerate it by re-running this script.

Usage: .venv/bin/python forms_in_progress/run_all.py
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from registry import FORMS, data_path, output_dir
from verify import build_rows
from forms.fill import fill_pdf_form, _load


def main():
    out = output_dir()
    all_reports = {}

    for city_key, cfg in FORMS.items():
        city_data_path = data_path(city_key)
        if not city_data_path.exists():
            print(f"{cfg['display_name']:20s} SKIPPED — no permit_data.json yet (run build_data.py first)")
            continue
        data = _load(city_data_path)

        city_out = out / city_key
        city_out.mkdir(parents=True, exist_ok=True)

        for form_name, form_cfg in cfg["forms"].items():
            key = f"{city_key}/{form_name}"
            pdf_out = city_out / f"{form_name}_filled.pdf"
            try:
                report = fill_pdf_form(
                    pdf_path=form_cfg["template"],
                    data_path=city_data_path,
                    mapping_path=form_cfg["mapping"],
                    output_path=pdf_out,
                )
                all_reports[key] = report
                print(f"{key:35s} status={report['status']:14s} "
                      f"filled={len(report['filled_pdf_fields']):3d} issues={len(report['issues'])}")
            except Exception as e:
                all_reports[key] = {"status": "ERROR", "error": str(e)}
                print(f"{key:35s} ERROR: {e}")
                continue

            rows = build_rows(data, form_cfg["mapping"], form_cfg["template"])
            csv_path = city_out / f"VERIFY_{form_name}.csv"
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["pdf_field", "schema_key", "jobnimbus_source", "value", "status"])
                writer.writerows(rows)

    reports_path = out / "fill_reports.json"
    reports_path.write_text(json.dumps(all_reports, indent=2))
    print(f"\nAll output written to {out}")

    failed = [k for k, r in all_reports.items() if r.get("status") not in ("passed", "needs_review")]
    if failed:
        print(f"\n{len(failed)} form(s) failed to fill entirely: {failed}")


if __name__ == "__main__":
    main()
