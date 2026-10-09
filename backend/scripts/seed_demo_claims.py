"""Seed realistic claims for local demos and frontend development."""

import sys

from backend.engine import (
    RuleResult,
    ValidationResult,
    get_all_claims,
    init_db,
    save_claim,
    update_claim_decision,
)
from backend.gemma_client import ClaimExtraction, LineItem


def build_demo_claims() -> list[tuple[str, ClaimExtraction, ValidationResult, str]]:
    return [
        (
            "expense",
            ClaimExtraction(
                provider_name="Starbucks Coffee",
                patient_or_employee_name="Aarav Mehta",
                date_extracted="2026-10-09",
                currency="INR",
                items=[LineItem(description="Coffee and breakfast", amount=450.0, category="meals")],
                total_extracted=450.0,
                confidence_score=0.98,
            ),
            ValidationResult(
                is_valid=True,
                final_amount_inr=450.0,
                results=[
                    RuleResult(
                        rule_name="Policy Limit",
                        passed=True,
                        message="₹450.00 is within the ₹4,000.00 demo policy limit.",
                    ),
                    RuleResult(
                        rule_name="Math Verification",
                        passed=True,
                        message="Line items sum perfectly to 450.0.",
                    ),
                ],
            ),
            "Approved",
        ),
        (
            "expense",
            ClaimExtraction(
                provider_name="Delta Airlines",
                patient_or_employee_name="Ishita Rao",
                date_extracted="2026-10-08",
                currency="USD",
                items=[LineItem(description="Business flight", amount=850.0, category="travel")],
                total_extracted=850.0,
                confidence_score=0.96,
            ),
            ValidationResult(
                is_valid=False,
                final_amount_inr=70975.0,
                results=[
                    RuleResult(
                        rule_name="Policy Limit",
                        passed=False,
                        message="Converted 850.0 USD to ₹70975.00, exceeding the ₹4,000.00 demo policy limit.",
                    ),
                    RuleResult(
                        rule_name="Math Verification",
                        passed=True,
                        message="Line items sum perfectly to 850.0.",
                    ),
                ],
            ),
            "Pending",
        ),
        (
            "health_insurance",
            ClaimExtraction(
                provider_name="Apollo Hospital Bangalore",
                patient_or_employee_name="Neha Kapoor",
                date_extracted="2026-10-07",
                currency="INR",
                items=[LineItem(description="Room rent", amount=18000.0, category="room_rent")],
                total_extracted=18000.0,
                confidence_score=0.97,
            ),
            ValidationResult(
                is_valid=False,
                final_amount_inr=18000.0,
                results=[
                    RuleResult(
                        rule_name="Room Rent Policy Cap",
                        passed=False,
                        message="Room rent ₹18000.00 exceeds the demo policy cap of ₹10000.00.",
                    ),
                    RuleResult(
                        rule_name="Consumables Compliance",
                        passed=True,
                        message="No excluded non-medical consumables found.",
                    ),
                ],
            ),
            "Pending",
        ),
        (
            "health_insurance",
            ClaimExtraction(
                provider_name="Fortis Healthcare",
                patient_or_employee_name="Rohan Shah",
                date_extracted="2026-10-06",
                currency="INR",
                items=[LineItem(description="Doctor consultation", amount=1500.0, category="doctor_fee")],
                total_extracted=1500.0,
                confidence_score=0.99,
            ),
            ValidationResult(
                is_valid=True,
                final_amount_inr=1500.0,
                results=[
                    RuleResult(
                        rule_name="Room Rent Policy Cap",
                        passed=True,
                        message="No room rent item requires a cap review.",
                    ),
                    RuleResult(
                        rule_name="Consumables Compliance",
                        passed=True,
                        message="No excluded non-medical consumables found.",
                    ),
                ],
            ),
            "Approved",
        ),
    ]


def seed_demo_claims() -> int:
    init_db()
    existing_providers = {
        claim["extracted_data"].get("provider_name")
        for claim in get_all_claims()
    }
    inserted = 0

    for domain, extracted_data, validation, status in build_demo_claims():
        provider_name = extracted_data.provider_name
        if provider_name in existing_providers:
            continue

        claim_id = save_claim(domain, extracted_data, validation)
        if status != "Pending":
            update_claim_decision(claim_id, status)
        existing_providers.add(provider_name)
        inserted += 1

    return inserted


if __name__ == "__main__":
    seed_demo_claims()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("✅ Successfully seeded 4 demo claims into ClaimGuard database!")
