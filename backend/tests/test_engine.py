import pytest
from backend.engine import run_deterministic_checks
from backend.gemma_client import ClaimExtraction, LineItem

def test_valid_expense():
    # Setup mock valid data
    mock_data = ClaimExtraction(
        provider_name="Test Vendor",
        patient_or_employee_name="John Doe",
        date_extracted="2026-10-09",
        currency="INR",
        items=[LineItem(description="Lunch", amount=500.0)],
        total_extracted=500.0,
        confidence_score=0.9
    )
    # Different image bytes so hash doesn't trigger duplicate
    result = run_deterministic_checks(mock_data, b"fake_image_bytes_1", "{}", "expense")
    assert result.is_valid == True
    assert result.final_amount_inr == 500.0

def test_over_limit_expense():
    mock_data = ClaimExtraction(
        provider_name="Test Vendor",
        patient_or_employee_name="John Doe",
        date_extracted="2026-10-09",
        currency="USD",
        items=[LineItem(description="Expensive Dinner", amount=100.0)],
        total_extracted=100.0,
        confidence_score=0.9
    )
    # USD 100 * 83.5 = 8350 INR (over the default 4000 limit)
    result = run_deterministic_checks(mock_data, b"fake_image_bytes_2", "{}", "expense")
    assert result.is_valid == False
    assert any("EXCEEDS policy limit" in r.message for r in result.results)

def test_duplicate_fraud():
    mock_data = ClaimExtraction(
        provider_name="Test Vendor",
        patient_or_employee_name="John",
        date_extracted="2026-10-09",
        currency="INR",
        items=[LineItem(description="Lunch", amount=500.0)],
        total_extracted=500.0,
        confidence_score=0.9
    )
    # Send the same exact bytes twice
    result1 = run_deterministic_checks(mock_data, b"duplicate_bytes", "{}", "expense")
    result2 = run_deterministic_checks(mock_data, b"duplicate_bytes", "{}", "expense")
    
    # First should pass fraud check
    assert any("unique" in r.message for r in result1.results if r.rule_name == "Fraud Detection")
    
    # Second should fail fraud check
    assert result2.is_valid == False
    assert any("DUPLICATE DETECTED" in r.message for r in result2.results if r.rule_name == "Fraud Detection")

def test_health_insurance_consumables():
    mock_data = ClaimExtraction(
        provider_name="Test Hospital",
        patient_or_employee_name="Jane Doe",
        date_extracted="2026-10-09",
        currency="INR",
        items=[
            LineItem(description="Room Rent", amount=2000.0, category="room_rent"),
            LineItem(description="Gloves", amount=500.0, category="consumables")
        ],
        total_extracted=2500.0,
        confidence_score=0.9
    )
    result = run_deterministic_checks(mock_data, b"fake_image_bytes_4", "{}", "health_insurance")
    assert result.is_valid == False
    assert any("Consumables Excluded" in r.rule_name for r in result.results)
