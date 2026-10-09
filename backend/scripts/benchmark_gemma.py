"""Benchmark ClaimGuard extraction backends across both supported domains."""

import argparse
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.gemma_client import ClaimExtraction, extract_form_data, get_model_status


SYNTHETIC_DOCUMENT = b"ClaimGuard synthetic health bill: Fortis Healthcare total INR 1500"


@contextmanager
def temporary_environment(**changes: str | None):
    original = {key: os.environ.get(key) for key in changes}
    try:
        for key, value in changes.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def validate_extraction(value: ClaimExtraction) -> bool:
    """Validate required evidence fields through the Pydantic model contract."""
    if not isinstance(value, ClaimExtraction):
        return False
    return bool(
        value.provider_name.strip()
        and value.currency.strip()
        and isinstance(value.items, list)
        and all(item.description.strip() and item.amount >= 0 for item in value.items)
        and value.total_extracted >= 0
        and 0 <= value.confidence_score <= 1
    )


def run_case(label: str, domain: str, runs: int, *, force_mock: bool = False, force_local: bool = False) -> dict:
    status = get_model_status()
    if force_mock:
        changes = {"GEMINI_API_KEY": None, "USE_LOCAL_LLM": None}
        payload = b""
    elif force_local:
        if status["local_ollama_online"]:
            changes = {"GEMINI_API_KEY": None, "USE_LOCAL_LLM": "1"}
            payload = SYNTHETIC_DOCUMENT
        else:
            changes = {"GEMINI_API_KEY": None, "USE_LOCAL_LLM": None}
            payload = b""
    else:
        changes = {}
        payload = SYNTHETIC_DOCUMENT if status["cloud_gemma_available"] or status["local_ollama_online"] else b""

    latencies = []
    result = None
    model_used = label
    with temporary_environment(**changes):
        for _ in range(runs):
            started = time.perf_counter()
            result = extract_form_data(payload, "image/png", "Synthetic benchmark document", domain)
            latencies.append((time.perf_counter() - started) * 1000)

    extraction, fallback, source = result
    schema_valid = validate_extraction(extraction)
    if source == "offline_mock":
        connection = "Offline"
    elif source.startswith("local_ollama"):
        connection = "Online" if status["local_ollama_online"] else "Offline"
    else:
        connection = "Online" if status["cloud_gemma_available"] else "Offline"

    return {
        "domain": domain,
        "backend": source or model_used,
        "status": connection,
        "latency": sum(latencies) / len(latencies),
        "schema": "Yes" if schema_valid else "No",
        "confidence": f"{extraction.confidence_score:.2f}",
        "fallback": "Yes" if fallback else "No",
        "items": len(extraction.items),
        "total": f"{extraction.total_extracted:.2f}",
    }


def print_table(rows: list[dict]) -> None:
    headers = ["Domain", "Backend", "Status", "Latency (ms)", "Schema", "Confidence", "Fallback", "Items", "Total"]
    keys = ["domain", "backend", "status", "latency", "schema", "confidence", "fallback", "items", "total"]
    values = []
    for row in rows:
        values.append([
            row["domain"], row["backend"], row["status"], f"{row['latency']:.1f}",
            row["schema"], row["confidence"], row["fallback"], str(row["items"]), row["total"],
        ])
    widths = [max(len(header), *(len(value[index]) for value in values)) for index, header in enumerate(headers)]
    separator = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    print(separator)
    print("|" + "|".join(f" {header:<{width}} " for header, width in zip(headers, widths)) + "|")
    print(separator)
    for row in values:
        print("|" + "|".join(f" {value:<{width}} " for value, width in zip(row, widths)) + "|")
    print(separator)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark ClaimGuard Gemma extraction backends.")
    parser.add_argument("--runs", type=int, default=1, help="Iterations per benchmark case (default: 1)")
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be at least 1")

    rows = []
    for domain in ("expense", "health_insurance"):
        rows.append(run_case("configured", domain, args.runs))
        rows.append(run_case("local_ollama", domain, args.runs, force_local=True))
        rows.append(run_case("offline_mock", domain, args.runs, force_mock=True))
    print_table(rows)
    return 0 if all(row["schema"] == "Yes" for row in rows) else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
