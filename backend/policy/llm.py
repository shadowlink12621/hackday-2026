import json
import os
import re
from typing import Type
from pydantic import BaseModel

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def get_active_tier(allow_cloud_processing: bool = False):
    api_key = os.environ.get("GEMINI_API_KEY")
    use_local_llm = os.environ.get("USE_LOCAL_LLM", "").lower() in ("1", "true", "yes")
    if allow_cloud_processing and HAS_GENAI and api_key and not use_local_llm:
        return "cloud_gemma"
    return "offline_mock"

def generate_json(
    prompt: str,
    schema_cls: Type[BaseModel],
    images=None,
    allow_cloud_processing: bool = False,
    document_uri: str | None = None,
) -> tuple[BaseModel, str, bool]:
    """Generates structured JSON using Gemma."""
    tier = get_active_tier(allow_cloud_processing)
    if tier == "cloud_gemma":
        try:
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            model_name = os.environ.get("GEMINI_MODEL") or os.environ.get("GEMMA_MODEL", "gemma-4-26b-a4b-it")
            json_schema = json.dumps(schema_cls.model_json_schema(), ensure_ascii=False)
            model_prompt = (
                f"{prompt}\n\nReturn only one JSON object matching this schema:\n{json_schema}"
            )
            contents = model_prompt
            if document_uri:
                from google.genai import types
                contents = [
                    types.Part.from_uri(file_uri=document_uri, mime_type="application/pdf"),
                    types.Part.from_text(text=model_prompt),
                ]
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
            )
            raw = (response.text or "").strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].removesuffix("```").strip()
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if match:
                raw = match.group(0)
            return schema_cls.model_validate(json.loads(raw)), f"cloud_gemma ({model_name})", False
        except Exception as e:
            if document_uri:
                raise
            print(f"Cloud generation failed: {e}")
            tier = "offline_mock"

    # Fallback to offline mock for test offline runs
    return schema_cls(), "offline_mock", True
