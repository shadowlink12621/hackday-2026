"""Validate one claim image from a terminal."""

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.engine import run_deterministic_checks
from backend.gemma_client import extract_form_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ClaimGuard validation on a receipt or medical bill.")
    parser.add_argument("--image", type=Path, help="Path to a .jpg, .jpeg, or .png image")
    parser.add_argument("--domain", choices=("expense", "health_insurance"), default="expense")
    parser.add_argument("--prompt", default="", help="Optional context for extraction")
    parser.add_argument("--limit", type=float, default=4000.0, help="Expense policy limit in INR")
    args = parser.parse_args()

    contents = b""
    mime_type = "image/png"
    if args.image:
        if args.image.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            parser.error("--image must have a .jpg, .jpeg, or .png extension")
        if not args.image.is_file():
            parser.error(f"Image file not found: {args.image}")
        contents = args.image.read_bytes()
        mime_type = "image/jpeg" if args.image.suffix.lower() in {".jpg", ".jpeg"} else "image/png"

    extracted, fallback, source = extract_form_data(contents, mime_type, args.prompt, args.domain)
    validation = run_deterministic_checks(
        extracted,
        contents,
        json.dumps({"policy_limit_inr": args.limit}),
        args.domain,
    )

    print("📋 Extracted Evidence")
    print(f"Provider: {extracted.provider_name}")
    print(f"Date: {extracted.date_extracted or 'Unknown'}")
    print(f"Currency: {extracted.currency}")
    print("Items:")
    for item in extracted.items:
        category = item.category or "uncategorized"
        print(f"  - {item.description} [{category}]: {item.amount:.2f}")
    print(f"Total: {extracted.total_extracted:.2f}")
    print(f"Model: {source} | Fallback: {'Yes' if fallback else 'No'}")
    print()
    print("⚙️ Policy Checks")
    for rule in validation.results:
        marker = "✅ PASS" if rule.passed else "❌ FAIL"
        print(f"{marker} | {rule.rule_name}: {rule.message}")
    print()
    verdict = "APPROVED" if validation.is_valid else "FLAGGED FOR REVIEW"
    print(f"🏁 Overall Verdict: {verdict}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
