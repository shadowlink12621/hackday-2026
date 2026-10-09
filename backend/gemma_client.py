import os
from pydantic import BaseModel
import json

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class FormExtraction(BaseModel):
    document_type: str
    has_signature: bool
    has_date: bool
    date_extracted: str | None
    has_official_stamp: bool
    confidence_score: float

def extract_form_data(file_bytes: bytes, mime_type: str, user_prompt: str, domain_mode: str) -> tuple[FormExtraction, bool]:
    """
    Uses Gemma 4 (via GenAI SDK) to analyze the document.
    Returns (FormExtraction, is_mock).
    Falls back to a mock deterministic response if API is unavailable.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    is_mock = True
    
    if HAS_GENAI and api_key and file_bytes:
        try:
            client = genai.Client(api_key=api_key)
            model = "gemini-2.5-flash" 
            
            prompt = f"""
            Domain Mode: {domain_mode}
            User Prompt: {user_prompt}
            
            Analyze this uploaded document.
            Identify the document type.
            Check if it has a physical or digital signature.
            Check if a date is written, and extract it if so.
            Check if there is an official stamp.
            Provide a confidence score between 0.0 and 1.0.
            """
            
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FormExtraction,
                    temperature=0.1
                )
            )
            
            is_mock = False
            return FormExtraction.model_validate_json(response.text), is_mock
        except Exception as e:
            print(f"GenAI API failed, falling back to mock. Error: {e}")
    
    # Fallback / Mock Mode
    print("Using offline mock mode (no API key, missing file, or API failed)")
    mock_data = FormExtraction(
        document_type=f"Mocked {domain_mode.capitalize()} Document",
        has_signature=True,
        has_date=True,
        date_extracted="2026-10-09",
        has_official_stamp=False,
        confidence_score=0.85
    )
    return mock_data, is_mock
