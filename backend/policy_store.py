"""Local, page-addressable storage and retrieval for uploaded policy PDFs."""

import hashlib
import re
import sqlite3
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from pypdf import PdfReader

from .engine import get_db_connection, with_db_retry

MAX_POLICY_PDF_BYTES = 20 * 1024 * 1024
MAX_POLICY_PAGES = 300
MAX_RETRIEVAL_PAGES = 5
STOP_WORDS = {
    "about", "after", "also", "and", "are", "can", "does", "for", "from",
    "have", "how", "into", "is", "may", "more", "not", "of", "on", "or",
    "should", "that", "the", "this", "what", "when", "where", "which", "with",
    "period", "policy", "insurance", "insurer", "insured", "claim", "cover",
    "coverage", "amount", "sum", "limit", "limits", "benefit", "section",
}
SENSITIVE_LABELS = re.compile(
    r"\b(insured name|patient name|member name|insured person details|primary insured|"
    r"member id|date of birth|\bdob\b|\bgender\b|\boccupation\b|nominee|"
    r"mobile number|phone number|e-?mail|address|pan no|aadhaar|policy number|"
    r"certificate number|abha number)\b",
    re.IGNORECASE,
)


def _redact_text(text: str) -> str:
    """Remove common direct identifiers before excerpts leave the local store."""
    safe_lines = [
        "[personal detail redacted]"
        if SENSITIVE_LABELS.search(line)
        or re.fullmatch(r"\s*[A-Z][A-Z.'-]{1,}(?:\s+[A-Z][A-Z.'-]{1,}){1,3}\s*", line)
        else line
        for line in text.splitlines()
    ]
    safe_text = "\n".join(safe_lines)
    safe_text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[email redacted]", safe_text)
    safe_text = re.sub(r"(?<!\d)(?:\+?91[ -]?)?[6-9]\d{9}(?!\d)", "[phone redacted]", safe_text)
    safe_text = re.sub(r"\b[A-Z]{5}\d{4}[A-Z]\b", "[identifier redacted]", safe_text, flags=re.IGNORECASE)
    safe_text = re.sub(r"\b\d{12}\b", "[identifier redacted]", safe_text)
    safe_text = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", "[date redacted]", safe_text)
    return safe_text


@with_db_retry
def init_policy_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                page_count INTEGER NOT NULL,
                insurer TEXT,
                imported_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS policy_pages (
                policy_id INTEGER NOT NULL,
                page_number INTEGER NOT NULL,
                page_text TEXT NOT NULL,
                PRIMARY KEY (policy_id, page_number),
                FOREIGN KEY (policy_id) REFERENCES policies(id) ON DELETE CASCADE
            )"""
        )


def _infer_insurer(all_text: str) -> str | None:
    text = all_text.lower()
    for insurer, markers in (
        ("SBI General", ("sbi general insurance", "sbi general")),
        ("HDFC ERGO", ("hdfc ergo",)),
        ("Star Health", ("star health",)),
        ("Niva Bupa", ("niva bupa",)),
        ("Care Health", ("care health insurance", "care health")),
        ("ICICI Lombard", ("icici lombard",)),
    ):
        if any(marker in text for marker in markers):
            return insurer
    return None


@with_db_retry
def ingest_policy_pdf(pdf_bytes: bytes, filename: str) -> dict[str, Any]:
    if not pdf_bytes or len(pdf_bytes) > MAX_POLICY_PDF_BYTES:
        raise ValueError("Policy PDF must be non-empty and no larger than 20 MB.")
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("The uploaded file is not a valid PDF document.")

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        if len(reader.pages) > MAX_POLICY_PAGES:
            raise ValueError(f"Policy PDFs are limited to {MAX_POLICY_PAGES} pages.")
        pages = [(i + 1, (page.extract_text() or "").strip()) for i, page in enumerate(reader.pages)]
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Could not read this PDF. Please check that it is not encrypted or damaged.") from exc

    nonempty = [(number, text) for number, text in pages if text]
    if not nonempty:
        raise ValueError("This PDF has no extractable text. Scanned PDFs need OCR before indexing.")

    content_hash = hashlib.sha256(pdf_bytes).hexdigest()
    insurer = _infer_insurer("\n".join(text for _, text in nonempty))
    init_policy_db()
    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT id, filename, page_count, insurer FROM policies WHERE content_hash = ?",
            (content_hash,),
        ).fetchone()
        if existing:
            policy_id = existing[0]
        else:
            cursor = conn.execute(
                "INSERT INTO policies (content_hash, filename, page_count, insurer, imported_at) VALUES (?, ?, ?, ?, ?)",
                (content_hash, filename, len(pages), insurer, datetime.now(timezone.utc).isoformat()),
            )
            policy_id = int(cursor.lastrowid)
            conn.executemany(
                "INSERT INTO policy_pages (policy_id, page_number, page_text) VALUES (?, ?, ?)",
                [(policy_id, number, text) for number, text in nonempty],
            )
        row = conn.execute(
            "SELECT id, filename, page_count, insurer, imported_at FROM policies WHERE id = ?",
            (policy_id,),
        ).fetchone()
    return {
        "policy_id": row[0],
        "filename": row[1],
        "page_count": row[2],
        "insurer": row[3],
        "imported_at": row[4],
        "duplicate_upload": bool(existing),
        "indexed_pages": len(nonempty),
    }


@with_db_retry
def get_policy(policy_id: int) -> dict[str, Any] | None:
    init_policy_db()
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, filename, page_count, insurer, imported_at FROM policies WHERE id = ?",
            (policy_id,),
        ).fetchone()
    if not row:
        return None
    policy = {
        "policy_id": row[0],
        "filename": row[1],
        "page_count": row[2],
        "insurer": row[3],
        "imported_at": row[4],
    }
    # Build this profile from the uploaded policy, not a particular insurer's demo fixture.
    profile_queries = (
        ("insurer product plan policy wording schedule version", "Policy identity and plan"),
        ("policy period inception date commencement expiry renewal", "Policy dates and renewal"),
        ("insured member name proposer relationship family members", "Insured members"),
        ("sum insured family floater individual cover available balance", "Sum insured and cover structure"),
        ("pre existing disease PED waiting period years", "Pre-existing condition waiting periods"),
        ("specific illness disease procedure waiting period", "Specific illness waiting periods"),
        ("general exclusions permanent exclusions not payable", "Exclusions"),
        ("room rent ICU limit cap proportionate deduction", "Room rent and ICU limits"),
        ("co-payment copay deductible threshold percentage", "Co-pay and deductible"),
        ("network hospital cashless provider hospital criteria", "Hospital network and eligibility"),
        ("pre hospitalization post hospitalization days", "Pre- and post-hospitalization benefits"),
        ("OPD outpatient dental optical vision benefit sublimit", "OPD, dental, and vision benefits"),
        ("consumables non medical items add-on payable", "Consumables and add-ons"),
        ("claim intimation submission documents discharge deadline reimbursement", "Claim process and required documents"),
        ("cataract refractive error eyesight lenses", "Eye-care terms"),
    )
    profile = []
    for query, topic in profile_queries:
        matches = retrieve_policy_pages(policy_id, query, limit=2)
        if matches:
            conflicting_room_text = any(
                "room rent limited" in match["text"].lower()
                and "no room rent capping" in match["text"].lower()
                for match in matches
            )
            profile.append({
                "topic": topic,
                "pages": [match["page"] for match in matches],
                "evidence": [match["text"][:1600] for match in matches],
                "status": "conflict_review" if conflicting_room_text else "source_found",
            })
    policy["profile"] = profile
    return policy


def retrieve_policy_pages(policy_id: int, question: str, limit: int = MAX_RETRIEVAL_PAGES) -> list[dict[str, Any]]:
    init_policy_db()
    terms = {
        token for token in re.findall(r"[a-z0-9]+", question.lower())
        if len(token) > 2 and token not in STOP_WORDS
    }
    if not terms:
        return []

    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT page_number, page_text FROM policy_pages WHERE policy_id = ?",
            (policy_id,),
        ).fetchall()

    scored = []
    for page_number, page_text in rows:
        normalized = re.sub(r"[^a-z0-9]+", " ", page_text.lower())
        score = sum(min(len(re.findall(rf"\b{re.escape(term)}\b", normalized)), 2) for term in terms)
        if score:
            scored.append((score, page_number, page_text))
    scored.sort(key=lambda entry: (-entry[0], entry[1]))
    results = []
    for score, page, text in scored[:max(1, min(limit, MAX_RETRIEVAL_PAGES))]:
        lines = text.splitlines()
        matching_indexes = [
            index for index, line in enumerate(lines)
            if any(term in re.sub(r"[^a-z0-9]+", " ", line.lower()) for term in terms)
        ]
        excerpt_lines = set()
        for index in matching_indexes:
            excerpt_lines.update(range(max(0, index - 1), min(len(lines), index + 2)))
        excerpt = "\n".join(lines[index] for index in sorted(excerpt_lines))
        results.append({"page": page, "score": score, "text": _redact_text(excerpt)[:3000]})
    return results
