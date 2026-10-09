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
    
    # New table to store full claims for the dashboard workflow
    c.execute('''CREATE TABLE IF NOT EXISTS claims
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  domain TEXT,
                  total_inr REAL,
                  is_valid BOOLEAN,
                  status TEXT DEFAULT 'Pending',
                  extracted_json TEXT,
                  verification_json TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

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
    rates = {"USD": 83.5, "EUR": 90.0, "INR": 1.0}
    return rates.get(currency.upper(), 1.0)

def save_claim(domain: str, extracted_data, validation: ValidationResult) -> int:
    """Saves the processed claim to the database and returns the ID."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO claims (domain, total_inr, is_valid, extracted_json, verification_json)
                 VALUES (?, ?, ?, ?, ?)''', 
              (domain, validation.final_amount_inr, validation.is_valid, 
               extracted_data.model_dump_json(), validation.model_dump_json()))
    claim_id = c.lastrowid
    conn.commit()
    conn.close()
    return claim_id

def get_all_claims():
    """Retrieves all claims from the DB."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM claims ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    
    claims = []
    for r in rows:
        claims.append({
            "id": r["id"],
            "domain": r["domain"],
            "total_inr": r["total_inr"],
            "is_valid": bool(r["is_valid"]),
            "status": r["status"],
            "extracted_data": json.loads(r["extracted_json"]),
            "verification_data": json.loads(r["verification_json"]),
            "timestamp": r["timestamp"]
        })
    return claims

def update_claim_decision(claim_id: int, decision: str):
    """Updates a claim's status (Approved/Rejected)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE claims SET status = ? WHERE id = ?", (decision, claim_id))
    conn.commit()
    conn.close()
    return True

def run_deterministic_checks(extracted_data, image_bytes: bytes, rule_settings_json: str, domain_mode: str) -> ValidationResult:
    results = []
    
    try:
        settings = json.loads(rule_settings_json)
    except:
        settings = {}
        
    policy_limit_inr = settings.get("policy_limit_inr", 4000.0)
    
    # 1. Fraud / Duplicate Check
    image_hash = hashlib.sha256(image_bytes).hexdigest() if image_bytes else "no-image-hash"
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT hash FROM receipts WHERE hash=?", (image_hash,))
    if c.fetchone() and image_bytes:
        results.append(RuleResult(rule_name="Fraud Detection", passed=False, message="🚨 DUPLICATE DETECTED! This document has already been processed."))
    else:
        results.append(RuleResult(rule_name="Fraud Detection", passed=True, message="Document hash is unique."))
        if image_bytes:
            c.execute("INSERT INTO receipts (hash) VALUES (?)", (image_hash,))
            conn.commit()
    conn.close()

    # 2. Math Verification
    calculated_total = sum(item.amount for item in extracted_data.items)
    if abs(calculated_total - extracted_data.total_extracted) < 0.01:
        results.append(RuleResult(rule_name="Math Verification", passed=True, message=f"Line items sum perfectly to {calculated_total}."))
    else:
        results.append(RuleResult(rule_name="Math Verification", passed=False, message=f"Math error! AI read total as {extracted_data.total_extracted}, but items sum to {calculated_total}."))

    # 3. Domain Specific Logic
    exchange_rate = get_exchange_rate(extracted_data.currency)
    final_amount_inr = calculated_total * exchange_rate
    
    if domain_mode == "health_insurance":
        room_rent_items = [item for item in extracted_data.items if item.category == "room_rent"]
        if room_rent_items:
            room_total = sum(i.amount for i in room_rent_items) * exchange_rate
            if room_total > 10000:
                results.append(RuleResult(rule_name="Room Rent Cap", passed=False, message=f"Room rent {room_total} INR exceeds standard cap. Requires manual review."))
            else:
                results.append(RuleResult(rule_name="Room Rent Cap", passed=True, message=f"Room rent {room_total} INR within limits."))
        
        consumables = [item for item in extracted_data.items if item.category == "consumables"]
        if consumables:
            results.append(RuleResult(rule_name="Consumables Excluded", passed=False, message="Non-medical consumables are not covered by standard policy."))
        else:
            results.append(RuleResult(rule_name="Consumables Check", passed=True, message="No non-medical consumables found."))
            
    else:
        msg = f"Converted {calculated_total} {extracted_data.currency} to {final_amount_inr} INR."
        if final_amount_inr <= policy_limit_inr:
            results.append(RuleResult(rule_name="Policy Limit", passed=True, message=f"{msg} Within policy limit of ₹{policy_limit_inr}."))
        else:
            results.append(RuleResult(rule_name="Policy Limit", passed=False, message=f"{msg} EXCEEDS policy limit of ₹{policy_limit_inr}!"))
        
    is_valid = all(r.passed for r in results)
    
    return ValidationResult(is_valid=is_valid, final_amount_inr=final_amount_inr, results=results)
