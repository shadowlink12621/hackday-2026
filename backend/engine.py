import functools
import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
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

    # 4. Local Insurer Knowledge Cross-Reference (If applicable)
    if domain_mode == "health_insurance":
        from .knowledge_loader import get_insurer_knowledge
        insurer_info = get_insurer_knowledge(extracted_data.provider_name)
        if insurer_info:
            for trap in insurer_info.get("key_traps", [])[:2]:
                results.append(
                    RuleResult(
                        rule_name=f"Built-in Insurer Guide ({insurer_info['title']})",
                        passed=True,
                        message=f"Reference guidance only; not extracted from this upload. {trap}",
                    )
                )

    return ValidationResult(
        is_valid=is_valid,
        final_amount_inr=final_amount_inr,
        results=results,
    )


def generate_claim_calendar_ics(claim: dict) -> str:
    """Generates an RFC 5545 .ics calendar reminder file for claim deadlines."""
    raw_date = claim.get("extracted_data", {}).get("date_extracted")
    base_dt = datetime.now()
    if raw_date:
        try:
            base_dt = datetime.strptime(str(raw_date)[:10], "%Y-%m-%d")
        except Exception:
            pass

    claim_id = claim.get("id", "1")
    vendor = claim.get("extracted_data", {}).get("provider_name", "Claim Provider")
    total = claim.get("total_inr", 0.0)

    deadline_dt = base_dt + timedelta(days=30)
    followup_dt = base_dt + timedelta(days=7)
    post_hosp_dt = base_dt + timedelta(days=90)

    def format_ics_date(dt: datetime) -> str:
        return dt.strftime("%Y%m%d")

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ClaimGuard//Claim Readiness & Benefit Navigator//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:claimguard-deadline-{claim_id}@claimguard.ai
DTSTAMP:{datetime.now().strftime("%Y%m%dT%H%M%SZ")}
DTSTART;VALUE=DATE:{format_ics_date(deadline_dt)}
DTEND;VALUE=DATE:{format_ics_date(deadline_dt + timedelta(days=1))}
SUMMARY:ClaimGuard reminder: verify document deadline for claim #{claim_id} ({vendor})
DESCRIPTION:Provisional reminder 30 days after the extracted document date. This is not a universal or statutory cutoff. Confirm the filing deadline in the active policy or with the insurer. Claim amount on record: INR {total:.2f}.
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:Reminder: Claim #{claim_id} document submission deadline tomorrow!
END:VALARM
END:VEVENT
BEGIN:VEVENT
UID:claimguard-followup-{claim_id}@claimguard.ai
DTSTAMP:{datetime.now().strftime("%Y%m%dT%H%M%SZ")}
DTSTART;VALUE=DATE:{format_ics_date(followup_dt)}
DTEND;VALUE=DATE:{format_ics_date(followup_dt + timedelta(days=1))}
SUMMARY:ClaimGuard checkpoint: follow up on claim #{claim_id} with TPA
DESCRIPTION:Provisional 7-day follow-up reminder. Confirm the expected response timeline with the insurer/TPA. Claim amount on record: INR {total:.2f}.
STATUS:CONFIRMED
END:VEVENT
BEGIN:VEVENT
UID:claimguard-posthosp-{claim_id}@claimguard.ai
DTSTAMP:{datetime.now().strftime("%Y%m%dT%H%M%SZ")}
DTSTART;VALUE=DATE:{format_ics_date(post_hosp_dt)}
DTEND;VALUE=DATE:{format_ics_date(post_hosp_dt + timedelta(days=1))}
SUMMARY:ClaimGuard reminder: check post-hospitalization benefit for claim #{claim_id}
DESCRIPTION:Provisional 90-day reminder to check the active policy's post-hospitalization benefit and submission requirements. This date is not a coverage guarantee.
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
"""
    return ics_content


def analyze_insurance_message(message_text: str) -> dict:
    """
    Analyzes an incoming SMS, email, or WhatsApp message for insurance fraud red flags.
    Cross-references IRDAI Bima Bharosa warnings against fee-for-settlement scams.
    """
    text_lower = message_text.lower()
    red_flags = []
    risk_score = 0

    fee_keywords = [
        "pay fee", "transfer fee", "processing charges", "gst charge to release",
        "refundable deposit", "pay rs", "pay inr", "clear tax to claim",
    ]
    if any(k in text_lower for k in fee_keywords) and any(w in text_lower for w in ["claim", "bonus", "fund", "settlement", "refund", "insurance"]):
        red_flags.append(
            "🚨 UPFRONT PAYMENT DEMAND: The message asks for money/fee to release an insurance claim. "
            "According to IRDAI Bima Bharosa guidelines, insurers NEVER ask policyholders for payment to release an approved claim or bonus."
        )
        risk_score += 45

    credential_keywords = ["otp", "upi pin", "scan qr", "qr code", "netbanking password", "card details", "cvv"]
    if any(k in text_lower for k in credential_keywords):
        red_flags.append(
            "🚨 SENSITIVE CREDENTIALS REQUESTED: Legitimate insurance claims never require you to share OTPs, "
            "enter your UPI PIN, or scan a payment QR code."
        )
        risk_score += 40

    guarantee_keywords = ["100% guaranteed approval", "guaranteed settlement", "government authorized private agent", "secret bonus"]
    if any(k in text_lower for k in guarantee_keywords):
        red_flags.append(
            "⚠️ SUSPICIOUS GUARANTEE: Legitimate claims undergo medical underwriter audit. "
            "Promises of 'guaranteed approval' from third parties often signal broker fraud."
        )
        risk_score += 20

    suspicious_links = ["bit.ly", "tinyurl", "wa.me", "t.me", ".xyz", ".top"]
    if any(k in text_lower for k in suspicious_links):
        red_flags.append(
            "⚠️ SUSPICIOUS LINK: Message contains an unverified shortlink or non-official domain "
            "instead of the insurer's registered portal."
        )
        risk_score += 15

    urgency_keywords = ["immediate action", "within 2 hours", "account will be blocked", "final notice", "lapse immediately"]
    if any(k in text_lower for k in urgency_keywords):
        red_flags.append(
            "⚠️ HIGH PRESSURE TACTICS: The sender uses urgency threats to rush you into acting "
            "without verifying with your insurer."
        )
        risk_score += 10

    risk_score = min(100, risk_score)
    if risk_score >= 40:
        risk_level = "HIGH_RISK"
        is_suspicious = True
        guidance = "DO NOT pay any money, share OTPs, or click links. Verify directly with your insurer's official helpline or register a grievance on IRDAI's Bima Bharosa portal."
    elif risk_score > 0:
        risk_level = "MEDIUM_RISK"
        is_suspicious = True
        guidance = "Exercise caution. Confirm the authenticity of this message with your insurer's official customer support before responding."
    else:
        risk_level = "SAFE"
        is_suspicious = False
        guidance = "No obvious red flags detected. Ensure any communication matches your official policy documents."

    return {
        "is_suspicious": is_suspicious,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "detected_red_flags": red_flags,
        "guidance": guidance,
        "official_portal_link": "https://bimabharosa.irdai.gov.in",
        "regulatory_reference": "IRDAI Consumer Protection Notice (No fee required for claim settlement)",
    }
