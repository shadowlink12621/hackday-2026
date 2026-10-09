import os
from pydantic import BaseModel, Field
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

class ReceiptExtraction(BaseModel):
    vendor_name: str
    date_extracted: str | None
    currency: str = Field(description="e.g. USD, INR, EUR")
    items: list[LineItem]
    total_extracted: float
    confidence_score: float

def extract_form_data(file_bytes: bytes, mime_type: str, user_prompt: str, domain_mode: str) -> tuple[ReceiptExtraction, bool]:
    """
    Uses Gemma 4 (via GenAI SDK) to analyze the receipt.
    Returns (ReceiptExtraction, is_mock).
    Falls back to a mock deterministic response if API is unavailable.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    is_mock = True
    
    if HAS_GENAI and api_key and file_bytes:
        try:
            client = genai.Client(api_key=api_key)
            model = "gemini-2.5-flash" 
            
            prompt = f"""
            Analyze this uploaded receipt.
            Extract the vendor name, date, and currency used.
            List all line items with their amounts.
            Extract the total amount as written on the receipt.
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
                    response_schema=ReceiptExtraction,
                    temperature=0.1
                )
            )
            
            is_mock = False
            return ReceiptExtraction.model_validate_json(response.text), is_mock
        except Exception as e:
            print(f"GenAI API failed, falling back to mock. Error: {e}")
    
    # Fallback / Mock Mode
    print("Using offline mock mode (no API key, missing file, or API failed)")
    mock_data = ReceiptExtraction(
        vendor_name="Starbucks (MOCKED)",
        date_extracted="2026-10-09",
        currency="USD",
        items=[
            LineItem(description="Venti Latte", amount=6.50),
            LineItem(description="Croissant", amount=3.50)
        ],
        total_extracted=10.00,
        confidence_score=0.92
    )
    return mock_data, is_mock
