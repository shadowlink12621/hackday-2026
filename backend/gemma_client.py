import os
from pydantic import BaseModel, Field
from typing import Optional, List
import json

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class LineItem(BaseModel):
    description: str
    amount: float
    category: Optional[str] = None # e.g. "meals", "room_rent", "consumables"

class ClaimExtraction(BaseModel):
    provider_name: str = Field(description="Vendor or Hospital name")
    patient_or_employee_name: Optional[str] = Field(description="Patient name for health, employee for expenses")
    date_extracted: Optional[str]
    currency: str = Field(description="e.g. USD, INR, EUR")
    items: List[LineItem]
    total_extracted: float
    confidence_score: float

def extract_form_data(file_bytes: bytes, mime_type: str, user_prompt: str, domain_mode: str) -> tuple[ClaimExtraction, bool]:
    """
    Uses Gemma 4 to analyze the receipt or health insurance claim.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    is_mock = True
    
    if HAS_GENAI and api_key and file_bytes:
        try:
            client = genai.Client(api_key=api_key)
            model = os.environ.get("GEMMA_MODEL", "gemma-4-26b-a4b-it")
            
            prompt = f"""
            Domain Mode: {domain_mode} (e.g. 'expense' or 'health_insurance')
            User Prompt: {user_prompt}
            
            Analyze this uploaded document.
            If it's an expense receipt: Extract the vendor name, date, currency, line items (with categories like 'meals', 'transport'), and total.
            If it's an Indian health insurance bill: Extract the hospital name (provider), patient name, date, currency (usually INR). For line items, carefully categorize them as 'room_rent', 'pharmacy', 'consumables', 'doctor_fee', etc. Extract the total.
            Provide a confidence score (0.0 to 1.0).
            """
            
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ClaimExtraction,
                    temperature=0.1
                )
            )
            
            is_mock = False
            return ClaimExtraction.model_validate_json(response.text), is_mock
        except Exception as e:
            print(f"GenAI API failed, falling back to mock. Error: {e}")
    
    # Fallback / Mock Mode
    print("Using offline mock mode")
    if domain_mode == "health_insurance":
        mock_data = ClaimExtraction(
            provider_name="Apollo Hospitals (MOCKED)",
            patient_or_employee_name="Rahul Sharma",
            date_extracted="2026-10-09",
            currency="INR",
            items=[
                LineItem(description="ICU Room Rent (2 days)", amount=20000, category="room_rent"),
                LineItem(description="Surgical Consumables (Gloves, Syringes)", amount=3500, category="consumables"),
                LineItem(description="Surgeon Fee", amount=45000, category="doctor_fee")
            ],
            total_extracted=68500.0,
            confidence_score=0.92
        )
    else:
        mock_data = ClaimExtraction(
            provider_name="Starbucks (MOCKED)",
            patient_or_employee_name="John Doe",
            date_extracted="2026-10-09",
            currency="USD",
            items=[
                LineItem(description="Venti Latte", amount=6.50, category="meals"),
                LineItem(description="Croissant", amount=3.50, category="meals")
            ],
            total_extracted=10.00,
            confidence_score=0.95
        )
    return mock_data, is_mock
