import os
from typing import Type
from pydantic import BaseModel

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def get_active_tier():
    api_key = os.environ.get("GEMINI_API_KEY")
    use_local_llm = os.environ.get("USE_LOCAL_LLM", "").lower() in ("1", "true", "yes")
    if HAS_GENAI and api_key and not use_local_llm:
        return "cloud_gemma"
    return "offline_mock"

def generate_json(prompt: str, schema_cls: Type[BaseModel], images=None) -> tuple[BaseModel, str, bool]:
    """Generates structured JSON using Gemma."""
    tier = get_active_tier()
    if tier == "cloud_gemma":
        try:
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            model_name = os.environ.get("GEMMA_MODEL", "gemini-2.5-flash")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema_cls,
                    temperature=0.1,
                )
            )
            return schema_cls.model_validate_json(response.text), f"cloud_gemma ({model_name})", False
        except Exception as e:
            print(f"Cloud generation failed: {e}")
            tier = "offline_mock"
    
    # Fallback to offline mock for test offline runs
    return schema_cls(), "offline_mock", True
