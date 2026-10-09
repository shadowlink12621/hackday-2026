import functools
import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, List, Optional
from pydantic import BaseModel

DB_FILE = os.environ.get("CLAIMGUARD_DB_FILE", "claimguard.db")
DB_TIMEOUT_SECONDS = float(os.environ.get("CLAIMGUARD_DB_TIMEOUT", "10.0"))
DB_MAX_RETRIES = int(os.environ.get("CLAIMGUARD_DB_RETRIES", "5"))


@contextmanager
def get_db_connection(timeout: float = DB_TIMEOUT_SECONDS):
    """Context manager providing an SQLite connection configured with WAL mode and busy timeout."""
    conn = sqlite3.connect(DB_FILE, timeout=timeout)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def with_db_retry(func):
    """Decorator to retry SQLite operations when database lock/busy errors occur."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        last_error = None
        for attempt in range(DB_MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError as exc:
                last_error = exc
                is_locked = "lock" in str(exc).lower() or "busy" in str(exc).lower()
                if is_locked and attempt < DB_MAX_RETRIES - 1:
                    time.sleep(0.05 * (2 ** attempt))
                    continue
                raise
        if last_error:
            raise last_error

    return wrapper


@with_db_retry
def init_db() -> None:
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS receipts
               (hash TEXT PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS claims
               (id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                total_inr REAL,
                is_valid BOOLEAN,
                status TEXT DEFAULT 'Pending',
                extracted_json TEXT,
                verification_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"""
        )


init_db()


class RuleResult(BaseModel):
    rule_name: str
    passed: bool
    message: str


class ValidationResult(BaseModel):
    is_valid: bool
    final_amount_inr: float
    results: List[RuleResult]


def get_exchange_rate(currency: str, custom_rates: dict[str, float] | None = None) -> Optional[float]:
    rates = {"USD": 83.5, "EUR": 90.0, "INR": 1.0, "GBP": 105.0}
    if custom_rates and isinstance(custom_rates, dict):
        rates.update({k.upper(): float(v) for k, v in custom_rates.items()})
    return rates.get(currency.upper(), None)




@with_db_retry
def save_claim(domain: str, extracted_data: Any, validation: ValidationResult) -> int:
    """Saves the processed claim to the database and returns the ID."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO claims (domain, total_inr, is_valid, extracted_json, verification_json)
               VALUES (?, ?, ?, ?, ?)""",
            (
                domain,
                validation.final_amount_inr,
                validation.is_valid,
                extracted_data.model_dump_json(),
                validation.model_dump_json(),
            ),
        )
        return int(c.lastrowid)


@with_db_retry
def get_all_claims() -> List[dict[str, Any]]:
    """Retrieves all claims from the DB."""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM claims ORDER BY id DESC")
        rows = c.fetchall()

    claims = []
    for r in rows:
        val_data = json.loads(r["verification_json"])
        claims.append(
            {
                "id": r["id"],
                "domain": r["domain"],
                "total_inr": r["total_inr"],
                "is_valid": bool(r["is_valid"]),
                "status": r["status"],
                "extracted_data": json.loads(r["extracted_json"]),
                "validation_data": val_data,
                "verification_data": val_data,
                "timestamp": r["timestamp"],
            }
        )
    return claims


@with_db_retry
def get_claim_by_id(claim_id: int) -> Optional[dict[str, Any]]:
    """Retrieves a single claim from the DB by ID."""
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM claims WHERE id = ?", (claim_id,))
        r = c.fetchone()
        
    if not r:
        return None
        
    val_data = json.loads(r["verification_json"])
    return {
        "id": r["id"],
        "domain": r["domain"],
        "total_inr": r["total_inr"],
        "is_valid": bool(r["is_valid"]),
        "status": r["status"],
        "extracted_data": json.loads(r["extracted_json"]),
        "validation_data": val_data,
        "verification_data": val_data,
        "timestamp": r["timestamp"],
    }


@with_db_retry
def update_claim_decision(claim_id: int, decision: str) -> bool:
    """Updates a claim's status (Approved/Rejected). Returns False if claim_id not found."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE claims SET status = ? WHERE id = ?", (decision, claim_id))
        return c.rowcount > 0


@with_db_retry
def check_and_record_receipt_hash(image_hash: str, has_image_bytes: bool) -> bool:
    """Checks for duplicate receipt hash and stores it if new. Returns True if duplicate."""
    if not has_image_bytes or image_hash == "no-image-hash":
        return False

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT hash FROM receipts WHERE hash = ?", (image_hash,))
        if c.fetchone():
            return True
        c.execute("INSERT OR IGNORE INTO receipts (hash) VALUES (?)", (image_hash,))
        return False


def run_deterministic_checks(
    extracted_data: Any,
    image_bytes: bytes,
    rule_settings_json: str,
    domain_mode: str,
) -> ValidationResult:
    results = []

    try:
        settings = json.loads(rule_settings_json)
    except Exception:
        settings = {}

    policy_limit_inr = float(settings.get("policy_limit_inr", 4000.0))
    custom_exchange_rates = settings.get("exchange_rates", {})

    # 1. Exact Duplicate Submission Check (SHA-256)
    image_hash = hashlib.sha256(image_bytes).hexdigest() if image_bytes else "no-image-hash"
    is_duplicate = check_and_record_receipt_hash(image_hash, bool(image_bytes))

    if is_duplicate:
        results.append(
            RuleResult(
                rule_name="Exact Duplicate Submission (SHA-256)",
                passed=False,
                message="🚨 DUPLICATE DETECTED! Exact document image hash already recorded in ledger.",
            )
        )
    else:
        results.append(
            RuleResult(
                rule_name="Exact Duplicate Submission (SHA-256)",
                passed=True,
                message="Document hash is unique in ledger.",
            )
        )

    # 2. Math Verification
    calculated_total = sum(item.amount for item in extracted_data.items)
    if abs(calculated_total - extracted_data.total_extracted) < 0.01:
        results.append(
            RuleResult(
                rule_name="Math Verification",
                passed=True,
                message=f"Line items sum perfectly to {calculated_total}.",
            )
        )
    else:
        results.append(
            RuleResult(
                rule_name="Math Verification",
                passed=False,
                message=(
                    f"Math error! AI read total as {extracted_data.total_extracted}, "
                    f"but items sum to {calculated_total}."
                ),
            )
        )

    # 3. Domain Specific Logic
    exchange_rate = get_exchange_rate(extracted_data.currency, custom_exchange_rates)
    if exchange_rate is None:
        results.append(
            RuleResult(
                rule_name="Currency Verification",
                passed=False,
                message=(
                    f"Unsupported currency '{extracted_data.currency}'. Supported currencies: "
                    "INR, USD, EUR, GBP. Manual exchange rate review required."
                ),
            )
        )
        final_amount_inr = calculated_total
        effective_rate = 1.0
    else:
        results.append(
            RuleResult(
                rule_name="Currency Verification",
                passed=True,
                message=f"Recognized currency {extracted_data.currency} (conversion rate: {exchange_rate}).",
            )
        )
        final_amount_inr = calculated_total * exchange_rate
        effective_rate = exchange_rate

    if domain_mode == "health_insurance":
        room_rent_cap_inr = float(settings.get("room_rent_cap_inr", 10000.0))
        disallow_consumables = not bool(settings.get("allow_consumables", False))

        room_rent_items = [item for item in extracted_data.items if item.category == "room_rent"]
        if room_rent_items:
            room_total = sum(i.amount for i in room_rent_items) * effective_rate
            if room_total > room_rent_cap_inr:
                results.append(
                    RuleResult(
                        rule_name="Room Rent Policy Cap",
                        passed=False,
                        message=f"Room rent ₹{room_total:.2f} exceeds policy cap of ₹{room_rent_cap_inr:.2f}. Requires manual approval.",
                    )
                )
            else:
                results.append(
                    RuleResult(
                        rule_name="Room Rent Policy Cap",
                        passed=True,
                        message=f"Room rent ₹{room_total:.2f} within policy cap of ₹{room_rent_cap_inr:.2f}.",
                    )
                )

        consumables = [item for item in extracted_data.items if item.category == "consumables"]
        if consumables and disallow_consumables:
            results.append(
                RuleResult(
                    rule_name="Non-Medical Consumables Exclusion",
                    passed=False,
                    message="Standard policy excludes non-medical consumables (gloves, syringes, sanitizers).",
                )
            )
        else:
            results.append(
                RuleResult(
                    rule_name="Consumables Compliance",
                    passed=True,
                    message="No excluded non-medical consumables found.",
                )
            )

    else:
        msg = f"Converted {calculated_total} {extracted_data.currency} to {final_amount_inr} INR."
        if final_amount_inr <= policy_limit_inr:
            results.append(
                RuleResult(
                    rule_name="Policy Limit",
                    passed=True,
                    message=f"{msg} Within policy limit of ₹{policy_limit_inr}.",
                )
            )
        else:
            results.append(
                RuleResult(
                    rule_name="Policy Limit",
                    passed=False,
                    message=f"{msg} EXCEEDS policy limit of ₹{policy_limit_inr}!",
                )
            )


    is_valid = all(r.passed for r in results)


    return ValidationResult(
        is_valid=is_valid,
        final_amount_inr=final_amount_inr,
        results=results,
    )
