from pydantic import BaseModel
from datetime import datetime
import json

class RuleResult(BaseModel):
    rule_name: str
    passed: bool
    message: str

class ValidationResult(BaseModel):
    is_valid: bool
    results: list[RuleResult]

def run_deterministic_checks(extracted_data, rule_settings_json: str) -> ValidationResult:
    """
    Takes the structured data extracted by the AI and runs deterministic, 
    verifiable software rules against it.
    """
    results = []
    
    # Optional: parse rule settings (e.g. strict_mode)
    try:
        settings = json.loads(rule_settings_json)
    except:
        settings = {}
        
    strict_mode = settings.get("strict_mode", False)
    
    # Check 1: Must have a signature
    if extracted_data.has_signature:
        results.append(RuleResult(rule_name="Signature Check", passed=True, message="Signature detected."))
    else:
        results.append(RuleResult(rule_name="Signature Check", passed=False, message="Missing signature. Application invalid."))
        
    # Check 2: Must have a date
    if extracted_data.has_date and extracted_data.date_extracted:
        results.append(RuleResult(rule_name="Date Check", passed=True, message=f"Date found: {extracted_data.date_extracted}"))
    else:
        results.append(RuleResult(rule_name="Date Check", passed=False, message="Missing date."))
        
    # Check 3: Must have official stamp (only fail in strict mode if missing)
    if extracted_data.has_official_stamp:
        results.append(RuleResult(rule_name="Stamp Check", passed=True, message="Official stamp verified."))
    else:
        if strict_mode:
            results.append(RuleResult(rule_name="Stamp Check", passed=False, message="No official stamp found. Document is unverified."))
        else:
            results.append(RuleResult(rule_name="Stamp Check", passed=True, message="No official stamp, but allowed in loose mode."))
        
    # Check 4: AI Confidence threshold
    if extracted_data.confidence_score >= 0.7:
        results.append(RuleResult(rule_name="AI Confidence Check", passed=True, message=f"High confidence ({extracted_data.confidence_score*100:.0f}%)"))
    else:
        results.append(RuleResult(rule_name="AI Confidence Check", passed=False, message=f"Low AI confidence ({extracted_data.confidence_score*100:.0f}%), manual review required."))

    # Aggregate result
    is_valid = all(r.passed for r in results)
    
    return ValidationResult(is_valid=is_valid, results=results)
