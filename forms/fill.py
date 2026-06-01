"""PDF AcroForm filling via PyMuPDF. Adapted from the original pdf_form_tool.py."""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

TRUE_VALUES = {True, "true", "True", "yes", "Yes", "y", "Y", "1", 1, "on", "On"}
FALSE_VALUES = {False, "false", "False", "no", "No", "n", "N", "0", 0, "off", "Off", None, ""}


@dataclass
class FillIssue:
    severity: str
    field: str
    message: str

    def as_dict(self):
        return {"severity": self.severity, "field": self.field, "message": self.message}


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_nested(data, dotted_key, default=None):
    cur = data
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _normalize(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v is not None)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _split_phone(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) >= 10:
        return digits[-10:-7], f"{digits[-7:-4]}-{digits[-4:]}"
    return "", str(value or "")


def _wrap_to_fields(value, count, width):
    text = _normalize(value)
    lines = textwrap.wrap(text, width=width, break_long_words=False, replace_whitespace=False) or [text]
    lines = lines[:count]
    return lines + [""] * (count - len(lines))


def _build_updates(data, mapping, available):
    updates, issues = {}, []

    for schema_key, spec in mapping.get("fields", {}).items():
        if isinstance(spec, str):
            spec = {"pdf_field_name": spec}

        required = bool(spec.get("required", False))
        value = _get_nested(data, schema_key)

        if value is None or value == "":
            if "default" in spec:
                value = spec["default"]
            elif required:
                issues.append(FillIssue("error", schema_key, "Required value missing."))
                continue
            else:
                continue

        transform = spec.get("transform")

        if transform == "phone_area_rest":
            names = spec.get("pdf_field_names", [])
            parts = _split_phone(value)
            for name, part in zip(names, parts):
                if name not in available:
                    issues.append(FillIssue("error", schema_key, f"PDF field not found: {name}"))
                    continue
                updates[name] = {"value": part, "type": "text", "schema_key": schema_key}
            continue

        if "pdf_field_names" in spec:
            names = spec["pdf_field_names"]
            parts = _wrap_to_fields(value, len(names), int(spec.get("wrap_width", 90)))
            for name, part in zip(names, parts):
                if name not in available:
                    issues.append(FillIssue("error", schema_key, f"PDF field not found: {name}"))
                    continue
                updates[name] = {"value": part, "type": "text", "schema_key": schema_key}
            continue

        name = spec.get("pdf_field_name")
        if not name:
            issues.append(FillIssue("error", schema_key, "Spec missing pdf_field_name."))
            continue
        if name not in available:
            issues.append(FillIssue("error", schema_key, f"PDF field not found: {name}"))
            continue

        updates[name] = {"value": value, "type": spec.get("type", "auto"), "schema_key": schema_key}

    return updates, issues


def _set_checkbox(widget, value):
    if value in TRUE_VALUES:
        try:
            widget.field_value = widget.on_state() or "Yes"
        except Exception:
            widget.field_value = "Yes"
    else:
        widget.field_value = False
    widget.update()


def _apply(doc, updates):
    filled = []
    for page in doc:
        for widget in page.widgets() or []:
            if widget.field_name not in updates:
                continue
            upd = updates[widget.field_name]
            value = upd["value"]
            req_type = upd.get("type", "auto")
            wtype = widget.field_type_string

            if req_type == "checkbox" or wtype == "CheckBox":
                _set_checkbox(widget, value)
                filled.append(widget.field_name)
                continue

            if req_type == "radio" or wtype == "RadioButton":
                desired = _normalize(value).strip().lower()
                try:
                    on_state = str(widget.on_state() or "")
                except Exception:
                    on_state = ""
                widget.field_value = widget.on_state() if on_state.strip().lower() == desired else False
                widget.update()
                filled.append(widget.field_name)
                continue

            widget.field_value = _normalize(value)
            widget.update()
            filled.append(widget.field_name)

    return sorted(set(filled))


def fill_pdf_form(pdf_path, data_path, mapping_path, output_path, flatten=False):
    data = _load(data_path)
    mapping = _load(mapping_path)

    doc = fitz.open(pdf_path)
    available = {w.field_name for page in doc for w in (page.widgets() or [])}

    if not available:
        raise RuntimeError("No fillable fields found in PDF.")

    updates, issues = _build_updates(data, mapping, available)
    filled = _apply(doc, updates)

    if flatten:
        for page in doc:
            page.wrap_contents()
            for w in list(page.widgets() or []):
                page.delete_widget(w)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path, incremental=False, deflate=True, garbage=4)
    doc.close()

    not_filled = sorted(set(updates.keys()) - set(filled))
    for name in not_filled:
        issues.append(FillIssue("error", name, "Expected field was not filled."))

    status = "passed" if not any(i.severity == "error" for i in issues) else "needs_review"
    return {
        "status": status,
        "input_pdf": str(pdf_path),
        "output_pdf": str(output_path),
        "expected_pdf_fields": sorted(updates.keys()),
        "filled_pdf_fields": filled,
        "issues": [i.as_dict() for i in issues],
    }
