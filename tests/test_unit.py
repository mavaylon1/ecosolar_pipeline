"""
Tier 1 — Unit tests. No JNB calls, no external dependencies.
Tests transformer logic, calculations, and field parsing in isolation.
"""

import pytest
from pipeline.transformer import (
    build_permit_data,
    _calc_valuation,
    _parse_structures,
    _use_type,
    _job_address,
)

# ── Valuation ──────────────────────────────────────────────────────────────

def test_valuation_ac_kw_no_batteries():
    job = {"system_kw_ac": "7.2", "Number of Battery": 0}
    assert _calc_valuation(job) == "14000"  # round(7.2)=7, 7×2000

def test_valuation_rounds_up():
    job = {"system_kw_ac": "7.6", "Number of Battery": 0}
    assert _calc_valuation(job) == "16000"  # round(7.6)=8, 8×2000

def test_valuation_rounds_down():
    job = {"system_kw_ac": "7.2", "Number of Battery": 0}
    assert _calc_valuation(job) == "14000"  # round(7.2)=7

def test_valuation_with_batteries():
    job = {"system_kw_ac": "7.2", "Number of Battery": 1}
    assert _calc_valuation(job) == "16500"  # 7×2000 + 1×2500

def test_valuation_multiple_batteries():
    job = {"system_kw_ac": "7.2", "Number of Battery": 2}
    assert _calc_valuation(job) == "19000"  # 7×2000 + 2×2500

def test_valuation_falls_back_to_dc():
    job = {"System size DC": 2.64, "Number of Battery": 0}
    assert _calc_valuation(job) == "6000"  # round(2.64)=3, 3×2000

def test_valuation_ac_preferred_over_dc():
    job = {"system_kw_ac": "7.2", "System size DC": 2.64, "Number of Battery": 0}
    assert _calc_valuation(job) == "14000"  # uses AC not DC

def test_valuation_missing_kw():
    assert _calc_valuation({}) == ""

def test_valuation_no_battery_key():
    job = {"system_kw_ac": "7.2"}
    assert _calc_valuation(job) == "14000"  # missing battery treated as 0


# ── Structure parsing ──────────────────────────────────────────────────────

def test_structure_main_only():
    result = _parse_structures("Main")
    assert result == {"main_structure": True, "garage": False, "patio": False, "accessory_structure": False}

def test_structure_multiple():
    result = _parse_structures("Main,Garage")
    assert result["main_structure"] is True
    assert result["garage"] is True
    assert result["patio"] is False

def test_structure_all():
    result = _parse_structures("Main,Garage,Patio,Accessory Structure")
    assert all(result.values())

def test_structure_case_insensitive():
    assert _parse_structures("main")["main_structure"] is True
    assert _parse_structures("GARAGE")["garage"] is True

def test_structure_with_spaces():
    result = _parse_structures("Main, Garage, Patio")
    assert result["main_structure"] is True
    assert result["garage"] is True

def test_structure_empty():
    result = _parse_structures(None)
    assert not any(result.values())

def test_structure_accessory_short():
    assert _parse_structures("Accessory")["accessory_structure"] is True


# ── Property type / use type ───────────────────────────────────────────────

def test_use_type_single_family():
    assert _use_type({"Property Type": "Single Family"}) == {"residential": True, "commercial": False}

def test_use_type_commercial_building():
    assert _use_type({"Property Type": "Commercial Building"}) == {"residential": False, "commercial": True}

def test_use_type_townhome():
    assert _use_type({"Property Type": "Townhome"}) == {"residential": True, "commercial": False}

def test_use_type_empty():
    assert _use_type({}) == {"residential": True, "commercial": False}


# ── Job address ────────────────────────────────────────────────────────────

def test_job_address_full():
    job = {"address_line1": "123 Main St", "city": "Garden Grove", "state_text": "CA", "zip": "92840"}
    assert _job_address(job) == "123 Main St, Garden Grove, CA, 92840"

def test_job_address_missing_zip():
    job = {"address_line1": "123 Main St", "city": "Garden Grove", "state_text": "CA"}
    assert _job_address(job) == "123 Main St, Garden Grove, CA"

def test_job_address_empty():
    assert _job_address({}) == ""


# ── Full transformer ───────────────────────────────────────────────────────

_MOCK_JOB = {
    "jnid": "test123",
    "name": "Test Job",
    "address_line1": "123 Main St",
    "city": "Garden Grove",
    "state_text": "CA",
    "zip": "92840",
    "Property Type": "Single Family",
    "Number Panels": 20,
    "Number of Battery": 1,
    "system_kw_ac": "7.2",
    "job_description": "Install solar PV system.",
    "structure": "Main",
    "existing_panels": "No",
}

_MOCK_CONTACT = {
    "first_name": "John",
    "last_name": "Smith",
    "home_phone": "7145550100",
    "email": "john@example.com",
}

def test_build_permit_data_owner():
    data = build_permit_data(_MOCK_JOB, _MOCK_CONTACT)
    assert data["owner"]["property_owner"] == "John Smith"
    assert data["owner"]["homeowner_phone"] == "7145550100"
    assert data["owner"]["homeowner_email"] == "john@example.com"

def test_build_permit_data_address():
    data = build_permit_data(_MOCK_JOB, _MOCK_CONTACT)
    assert data["property"]["job_address"] == "123 Main St, Garden Grove, CA, 92840"

def test_build_permit_data_valuation():
    data = build_permit_data(_MOCK_JOB, _MOCK_CONTACT)
    assert data["project"]["valuation"] == "16500"  # round(7.2)×2000 + 1×2500

def test_build_permit_data_solar():
    data = build_permit_data(_MOCK_JOB, _MOCK_CONTACT)
    assert data["solar"]["solar_panel_count"] == 20
    assert data["solar"]["solar_kw_ac"] == "7.2"
    assert data["solar"]["existing_solar_on_roof"] == "No"

def test_build_permit_data_structures():
    data = build_permit_data(_MOCK_JOB, _MOCK_CONTACT)
    assert data["reroof"]["structures"]["main_structure"] is True

def test_build_permit_data_permit_types():
    data = build_permit_data(_MOCK_JOB, _MOCK_CONTACT)
    assert data["project"]["permit_types"]["electrical"] is True
    assert data["project"]["permit_types"]["solar"] is True
    assert data["project"]["permit_types"]["building"] is False

def test_build_permit_data_static_contractor():
    data = build_permit_data(_MOCK_JOB, _MOCK_CONTACT)
    assert data["contractor"]["contractor_name"] == "Ecosolar USA Electric LLC"
    assert data["contractor"]["contractor_license"] == "1045300"

def test_build_permit_data_phone_fallback():
    contact = {"first_name": "Jane", "last_name": "Doe", "mobile_phone": "9995550100"}
    data = build_permit_data(_MOCK_JOB, contact)
    assert data["owner"]["homeowner_phone"] == "9995550100"
