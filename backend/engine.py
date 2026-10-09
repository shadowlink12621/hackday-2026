from pydantic import BaseModel
import json
import sqlite3
import hashlib
import os

DB_FILE = "claimguard.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS receipts 
                 (hash TEXT PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Initialize DB on load
init_db()

class RuleResult(BaseModel):
    rule_name: str
    passed: bool
    message: str

class ValidationResult(BaseModel):
    is_valid: bool
    final_amount_inr: float
    results: list[RuleResult]

def get_exchange_rate(currency: str) -> float:
    # In a real scenario, use requests.get("https://api.exchangerate-api.com/v4/latest/USD")
    # Using fixed rates to ensure demo stability
    rates = {"USD": 83.5, "EUR": 90.0, "INR": 1.0}
    return rates.get(currency.upper(), 1.0)

def run_deterministic_checks(extracted_data, image_bytes: bytes, rule_settings_json: str) -> ValidationResult:
    results = []
    
    # Optional settings
    try:
        settings = json.loads(rule_settings_json)
    except:
        settings = {}
        
    policy_limit_inr = settings.get("policy_limit_inr", 4000.0)
    
    # Check 1: Fraud / Duplicate Check
    image_hash = hashlib.sha256(image_bytes).hexdigest() if image_bytes else "no-image-hash"
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT hash FROM receipts WHERE hash=?", (image_hash,))
    if c.fetchone() and image_bytes:
        results.append(RuleResult(rule_name="Fraud Detection", passed=False, message="🚨 DUPLICATE DETECTED! This receipt has already been claimed."))
    else:
        results.append(RuleResult(rule_name="Fraud Detection", passed=True, message="Receipt hash is unique."))
        if image_bytes:
            c.execute("INSERT INTO receipts (hash) VALUES (?)", (image_hash,))
            conn.commit()
    conn.close()

    # Check 2: Math Verification
    calculated_total = sum(item.amount for item in extracted_data.items)
    if abs(calculated_total - extracted_data.total_extracted) < 0.01:
        results.append(RuleResult(rule_name="Math Verification", passed=True, message=f"Line items sum perfectly to {calculated_total}."))
    else:
        results.append(RuleResult(rule_name="Math Verification", passed=False, message=f"Math error! AI read total as {extracted_data.total_extracted}, but items sum to {calculated_total}."))

    # Check 3: Currency & Policy Limit
    exchange_rate = get_exchange_rate(extracted_data.currency)
    final_amount_inr = calculated_total * exchange_rate
    
    msg = f"Converted {calculated_total} {extracted_data.currency} to {final_amount_inr} INR."
    if final_amount_inr <= policy_limit_inr:
        results.append(RuleResult(rule_name="Policy Limit", passed=True, message=f"{msg} Within policy limit of ₹{policy_limit_inr}."))
    else:
        results.append(RuleResult(rule_name="Policy Limit", passed=False, message=f"{msg} EXCEEDS policy limit of ₹{policy_limit_inr}!"))
        
    # Aggregate result
    is_valid = all(r.passed for r in results)
    
    return ValidationResult(is_valid=is_valid, final_amount_inr=final_amount_inr, results=results)
