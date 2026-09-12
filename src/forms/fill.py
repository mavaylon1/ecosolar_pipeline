"""PDF AcroForm filling via PyMuPDF. Adapted from the original pdf_form_tool.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

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


def _get_font(font_name):
    try:
        return fitz.Font(fontname=(font_name or "helv").lower())
    except Exception:
        return fitz.Font(fontname="helv")


def _text_width(text, fontsize, font):
    return font.text_length(text, fontsize=fontsize)


def best_fit_fontsize(text, box_width, font, max_size=11, min_size=6, padding=4):
    """Largest font size (in half-point steps) at which `text` fits within box_width. Falls
    back to min_size (still may overflow) if even the smallest readable size doesn't fit."""
    if not text:
        return max_size
    usable = max(box_width - padding, 1)
    size = max_size
    while size > min_size and _text_width(text, size, font) > usable:
        size -= 0.5
    return size


def _wrap_by_width(text, box_width, fontsize, font, padding=4):
    """Greedy word-wrap using real font metrics instead of a guessed character count."""
    usable = max(box_width - padding, 1)
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if _text_width(candidate, fontsize, font) <= usable or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _wrap_to_fields(value, names, widget_lookup, wrap_fontsize=9):
    """Wraps `value` across `names` PDF fields using each field's real box width/font.
    Returns (parts_per_name, overflow_text_or_None) - overflow is any text that didn't
    fit even after using every available field, so callers can report it as a lost-data issue."""
    text = _normalize(value)
    count = len(names)

    widgets = [widget_lookup.get(n) for n in names]
    known_widths = [w.rect.width for w in widgets if w is not None]
    box_width = min(known_widths) if known_widths else 150
    font = _get_font(widgets[0].text_font if widgets and widgets[0] is not None else None)

    lines = _wrap_by_width(text, box_width, wrap_fontsize, font)
    overflow = None
    if len(lines) > count:
        lines, overflow_lines = lines[:count], lines[count:]
        overflow = " ".join(overflow_lines)
    parts = lines + [""] * (count - len(lines))
    return parts, overflow


def _build_updates(data, mapping, available, widget_lookup=None):
    updates, issues = {}, []
    widget_lookup = widget_lookup or {}

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
            wrap_fontsize = spec.get("fontsize", 9)
            parts, overflow = _wrap_to_fields(value, names, widget_lookup, wrap_fontsize=wrap_fontsize)
            if overflow:
                issues.append(FillIssue(
                    "warning", schema_key,
                    f"Text too long for the {len(names)} available field(s) - dropped: {overflow!r}",
                ))
            for name, part in zip(names, parts):
                if name not in available:
                    issues.append(FillIssue("error", schema_key, f"PDF field not found: {name}"))
                    continue
                updates[name] = {"value": part, "type": "text", "schema_key": schema_key, "fontsize": wrap_fontsize}
            continue

        name = spec.get("pdf_field_name")
        if not name:
            issues.append(FillIssue("error", schema_key, "Spec missing pdf_field_name."))
            continue
        if name not in available:
            issues.append(FillIssue("error", schema_key, f"PDF field not found: {name}"))
            continue

        updates[name] = {"value": value, "type": spec.get("type", "auto"), "schema_key": schema_key}
        if "fontsize" in spec:
            updates[name]["fontsize"] = spec["fontsize"]
        if "max_fontsize" in spec:
            updates[name]["max_fontsize"] = spec["max_fontsize"]

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
    overflow_issues = []
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

            text = _normalize(value)
            font = _get_font(widget.text_font)
            fontsize = upd.get("fontsize")
            if fontsize is None:
                # max_fontsize lowers the auto-fit ceiling for fields where the default 11pt
                # ceiling leaves razor-thin margin for typical values (e.g. a full address in
                # a narrow single-line box) - auto-shrink below that ceiling for longer values
                # still applies, this only caps how large it's allowed to start.
                fontsize = best_fit_fontsize(text, widget.rect.width, font, max_size=upd.get("max_fontsize", 11))
            usable = max(widget.rect.width - 4, 1)
            margin = usable - _text_width(text, fontsize, font)
            # A field that just barely fits (margin > 0 but under a real safety margin) still
            # reports zero issues if this only checks for literal overflow - that's exactly how
            # Fullerton's "Project Address" passed silently at a 0.3pt margin until someone
            # happened to audit it by hand. Anything under 3pt gets flagged now, not just
            # negative margin - genuine overflow is an error (breaks status), a thin-but-fitting
            # margin is a warning (worth a look, not a failure).
            if text and margin < 3:
                severity = "error" if margin < 0 else "warning"
                verb = "overflows" if margin < 0 else "has under 3pt margin in"
                overflow_issues.append(FillIssue(
                    severity, upd.get("schema_key", widget.field_name),
                    f"Value {verb} field {widget.field_name!r} at {fontsize}pt (margin={margin:.1f}pt): {text!r}",
                ))

            widget.text_fontsize = fontsize
            widget.field_value = text
            widget.update()
            filled.append(widget.field_name)

    return sorted(set(filled)), overflow_issues


def fill_pdf_form(pdf_path, data_path, mapping_path, output_path, flatten=False):
    data = _load(data_path)
    mapping = _load(mapping_path)

    doc = fitz.open(pdf_path)
    widget_lookup = {w.field_name: w for page in doc for w in (page.widgets() or [])}
    available = set(widget_lookup.keys())

    if not available:
        raise RuntimeError("No fillable fields found in PDF.")

    updates, issues = _build_updates(data, mapping, available, widget_lookup)
    filled, overflow_issues = _apply(doc, updates)
    issues.extend(overflow_issues)

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
