"""Knowledge base loader for insurer policies, sub-limits, and common claim traps."""

import os
from typing import Any, Dict, List, Optional

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")


def list_known_insurers() -> List[str]:
    """Returns list of insurer names available in local knowledge base."""
    insurers = []
    if os.path.exists(KNOWLEDGE_DIR):
        for fname in os.listdir(KNOWLEDGE_DIR):
            if fname.endswith(".md"):
                insurers.append(fname[:-3])
    return insurers


def get_insurer_knowledge(insurer_query: str) -> Optional[Dict[str, Any]]:
    """
    Finds insurer policy guide by fuzzy keyword match (e.g. 'hdfc', 'star', 'care').
    Returns parsed metadata, sub-limits, and avoidance gotchas.
    """
    if not os.path.exists(KNOWLEDGE_DIR) or not insurer_query:
        return None

    query_lower = insurer_query.lower()
    target_file = None

    for fname in os.listdir(KNOWLEDGE_DIR):
        if not fname.endswith(".md"):
            continue
        key = fname[:-3].lower()
        if key in query_lower or any(part in query_lower for part in key.split("_")):
            target_file = os.path.join(KNOWLEDGE_DIR, fname)
            break

    if not target_file:
        return None

    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        title = lines[0].replace("#", "").strip() if lines else "Insurer Guide"

        traps: List[str] = []
        is_traps_section = False
        for line in lines:
            if "Real-World Claim Repudiation Traps" in line:
                is_traps_section = True
                continue
            if is_traps_section and line.startswith("#"):
                break
            if is_traps_section and line.strip().startswith(("1.", "2.", "3.", "4.", "-")):
                traps.append(line.strip())

        return {
            "insurer_key": os.path.basename(target_file)[:-3],
            "title": title,
            "raw_content": content,
            "key_traps": traps,
            "official_portal": "https://bimabharosa.irdai.gov.in",
        }
    except Exception as e:
        print(f"Error reading insurer knowledge: {e}")
        return None
