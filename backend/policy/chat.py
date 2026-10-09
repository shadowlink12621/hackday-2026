from pydantic import BaseModel, Field
from typing import List
import re
from .llm import generate_json

class Citation(BaseModel):
    page: int
    quote: str

class ChatResponse(BaseModel):
    answer: str = "Not found in the indexed excerpts."
    citations: List[Citation] = Field(default_factory=list)

def _extractive_answer(question: str, evidence: list) -> ChatResponse:
    """Use matching source text when no language model is configured."""
    stop_words = {
        "about", "after", "also", "and", "are", "can", "does", "for", "from",
        "have", "how", "into", "is", "may", "more", "not", "the", "this",
        "what", "when", "where", "which", "with", "policy", "insurance",
        "insured", "claim", "cover", "coverage", "please", "tell", "show",
    }
    terms = {
        term for term in re.findall(r"[a-z0-9]+", question.lower())
        if len(term) > 2 and term not in stop_words
    }
    candidates = []
    for item in evidence or []:
        text = str(item.get("text", item.get("quote", ""))).replace("\n", " ")
        for chunk in re.split(r"(?<=[.!?])\s+|(?<=;)\s+", text):
            chunk = re.sub(r"\s+", " ", chunk).strip(" •-\t")
            if len(chunk) < 20:
                continue
            normalized = re.sub(r"[^a-z0-9]+", " ", chunk.lower())
            score = sum(bool(re.search(rf"\b{re.escape(term)}\b", normalized)) for term in terms)
            if score:
                candidates.append((score, item.get("page"), chunk[:420]))
    candidates.sort(key=lambda item: (-item[0], item[1] or 0))
    excerpts = []
    citations = []
    seen = set()
    for _, page, quote in candidates:
        key = re.sub(r"\W+", " ", quote.lower())
        if key in seen:
            continue
        seen.add(key)
        excerpts.append(f"[Page {page}] {quote}" if page else quote)
        if page:
            citations.append(Citation(page=int(page), quote=quote))
        if len(excerpts) == 3:
            break
    if not excerpts:
        return ChatResponse(answer="I couldn't find wording that answers this question in the indexed excerpts. Try a more specific question or review the cited policy pages.")
    answer = "Relevant wording in the indexed policy:\n\n" + "\n\n".join(excerpts)
    answer += "\n\nThis is quoted policy text for guidance, not a coverage or claim-approval decision."
    return ChatResponse(answer=answer, citations=citations)

def answer(question, evidence=None, allow_cloud_processing=False, history=None) -> dict:
    """Answers a question based on policy chunks and profile."""
    evidence = evidence or []
    history = history or []
    dialogue = "\n".join(
        f"{turn['role']}: {turn['text']}" for turn in history
        if turn.get("role") in {"user", "assistant"} and turn.get("text")
    )
    prompt = f"""
    Answer the user's current question based ONLY on the provided policy chunks.
    Use prior dialogue only to resolve references in the current question; prior answers are not policy evidence.
    If the answer is not in the excerpts, say "Not found in the indexed excerpts."
    Do not invent answers or policies. Cite page numbers where facts are found.

    PRIOR DIALOGUE (context only):
    {dialogue or '[No prior turns]'}

    CHUNKS:
    {evidence}

    User Question: {question}
    """

    response_obj, model_used, is_fallback = generate_json(
        prompt, ChatResponse, allow_cloud_processing=allow_cloud_processing
    )

    if is_fallback:
        response_obj = _extractive_answer(question, evidence)
        model_used = "retrieval_only"

    return {
        "answer": response_obj.answer,
        "citations": [c.model_dump() for c in response_obj.citations],
        "model_used": model_used,
        "is_fallback": is_fallback
    }
