"""Validate the structure and fuzzy lookup coverage of insurer knowledge files."""

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.knowledge_loader import get_insurer_knowledge


KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge"
REQUIRED_SECTIONS = (
    "## 1. Plan Overview",
    "## 2. Key Sub-limits & Mandatory Policy Conditions",
    "## 3. Real-World Claim Repudiation Traps",
    "## 4. Statutory IRDAI Grievance Escalation",
)
QUERIES = ("hdfc", "star", "bupa", "care", "icici", "sbi")


def traps_in_section(content: str) -> list[str]:
    lines = content.splitlines()
    in_traps = False
    traps = []
    for line in lines:
        if REQUIRED_SECTIONS[2] in line:
            in_traps = True
            continue
        if in_traps and line.startswith("## "):
            break
        if in_traps and line.strip().startswith(("-", "1.", "2.", "3.", "4.")):
            traps.append(line.strip())
    return traps


def validate_file(path: Path) -> tuple[bool, list[str]]:
    if not path.is_file():
        return False, ["missing file"]
    content = path.read_text(encoding="utf-8")
    errors = []
    if len(content.encode("utf-8")) <= 500:
        errors.append("file is 500 bytes or smaller")
    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"missing {section}")
    traps = traps_in_section(content)
    if len(traps) < 3:
        errors.append(f"only {len(traps)} actionable traps found")
    if "Bima Bharosa" not in content:
        errors.append("missing Bima Bharosa reference")
    return not errors, traps if not errors else errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ClaimGuard insurer knowledge files.")
    parser.add_argument("--verbose", action="store_true", help="Print parsed repudiation traps")
    args = parser.parse_args()

    files = sorted(KNOWLEDGE_DIR.glob("*.md"))
    print("Insurer Knowledge Validation")
    print("+----------------------+--------+------------------------------+")
    print("| Insurer              | Status | Details                      |")
    print("+----------------------+--------+------------------------------+")
    all_passed = True
    for path in files:
        passed, details = validate_file(path)
        all_passed = all_passed and passed
        status = "✅ Passed" if passed else "❌ Failed"
        detail = f"{len(details)} traps" if passed else "; ".join(details)
        print(f"| {path.stem:<20} | {status:<6} | {detail:<28} |")
        if args.verbose and passed:
            for trap in details:
                print(f"|   trap: {trap[:64]:<64} |")
    print("+----------------------+--------+------------------------------+")

    for query in QUERIES:
        match = get_insurer_knowledge(query)
        passed = bool(match and match.get("key_traps"))
        all_passed = all_passed and passed
        print(f"Fuzzy lookup {query:<6}: {'✅ Passed' if passed else '❌ Failed'}")

    if len(files) != len(QUERIES):
        print(f"Expected {len(QUERIES)} insurer files, found {len(files)}.")
        all_passed = False
    return 0 if all_passed else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
