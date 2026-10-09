"""Local case and source-document persistence for the single-user demo."""

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .engine import get_db_connection, with_db_retry

DATA_DIR = Path(os.environ.get("CLAIMGUARD_DATA_DIR", "data")).resolve()
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}
DOCUMENT_CATEGORIES = {"policy", "lab_report", "discharge_summary", "bill", "prescription", "other"}


@with_db_retry
def init_case_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                patient_details_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                reminder_date TEXT,
                reminder_confirmed_at TEXT
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS case_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                policy_id INTEGER,
                uploaded_at TEXT NOT NULL
            )"""
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(cases)")}
        if "reminder_date" not in columns:
            conn.execute("ALTER TABLE cases ADD COLUMN reminder_date TEXT")
        if "reminder_confirmed_at" not in columns:
            conn.execute("ALTER TABLE cases ADD COLUMN reminder_confirmed_at TEXT")


def _document_record(row: Any) -> dict[str, Any]:
    return {
        "document_id": row[0], "category": row[1], "filename": row[2],
        "content_type": row[3], "size_bytes": row[4], "policy_id": row[5],
        "uploaded_at": row[6],
    }


@with_db_retry
def create_case(patient_name: str, details: dict[str, Any]) -> int:
    init_case_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO cases (patient_name, patient_details_json, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (patient_name.strip(), json.dumps(details), now, now),
        )
        return int(cursor.lastrowid)


@with_db_retry
def list_cases() -> list[dict[str, Any]]:
    init_case_db()
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, patient_name, patient_details_json, created_at, updated_at FROM cases ORDER BY updated_at DESC"
        ).fetchall()
        counts = {
            row[0]: row[1]
            for row in conn.execute("SELECT case_id, COUNT(*) FROM case_documents GROUP BY case_id")
        }
    return [
        {"case_id": r[0], "patient_name": r[1], "patient_details": json.loads(r[2]),
         "created_at": r[3], "updated_at": r[4], "document_count": counts.get(r[0], 0)}
        for r in rows
    ]


@with_db_retry
def get_case(case_id: int) -> dict[str, Any] | None:
    init_case_db()
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, patient_name, patient_details_json, created_at, updated_at, reminder_date, reminder_confirmed_at FROM cases WHERE id = ?",
            (case_id,),
        ).fetchone()
        if not row:
            return None
        documents = conn.execute(
            "SELECT id, category, original_filename, content_type, size_bytes, policy_id, uploaded_at "
            "FROM case_documents WHERE case_id = ? ORDER BY id",
            (case_id,),
        ).fetchall()
    return {
        "case_id": row[0], "patient_name": row[1], "patient_details": json.loads(row[2]),
        "created_at": row[3], "updated_at": row[4],
        "reminder_date": row[5], "reminder_confirmed_at": row[6],
        "documents": [_document_record(doc) for doc in documents],
    }


@with_db_retry
def save_case_reminder(case_id: int, reminder_date: str | None) -> bool:
    init_case_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.execute(
            "UPDATE cases SET reminder_date = ?, reminder_confirmed_at = ?, updated_at = ? WHERE id = ?",
            (reminder_date, now if reminder_date else None, now, case_id),
        )
        return cursor.rowcount > 0


@with_db_retry
def save_case_document(
    case_id: int, category: str, filename: str, content_type: str, contents: bytes, policy_id: int | None = None
) -> dict[str, Any] | None:
    if category not in DOCUMENT_CATEGORIES:
        raise ValueError("Unsupported document category.")
    if content_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValueError("Only PDF, JPEG, and PNG documents are supported.")
    if not contents or len(contents) > MAX_DOCUMENT_BYTES:
        raise ValueError("Document must be non-empty and no larger than 20 MB.")
    if content_type == "application/pdf" and not contents.startswith(b"%PDF"):
        raise ValueError("The uploaded document is not a valid PDF.")
    if content_type == "image/jpeg" and not contents.startswith(b"\xff\xd8\xff"):
        raise ValueError("The uploaded document is not a valid JPEG image.")
    if content_type == "image/png" and not contents.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("The uploaded document is not a valid PNG image.")

    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name).strip("._") or "document"
    stored_name = f"{uuid.uuid4().hex}{ALLOWED_DOCUMENT_TYPES[content_type]}"
    case_dir = DATA_DIR / "cases" / str(case_id)
    case_dir.mkdir(parents=True, exist_ok=True)
    destination = case_dir / stored_name
    init_case_db()
    with get_db_connection() as conn:
        exists = conn.execute("SELECT 1 FROM cases WHERE id = ?", (case_id,)).fetchone()
    if not exists:
        return None

    destination.write_bytes(contents)
    now = datetime.now(timezone.utc).isoformat()
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO case_documents (case_id, category, original_filename, stored_filename, content_type, "
                "size_bytes, policy_id, uploaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (case_id, category, safe_name, stored_name, content_type, len(contents), policy_id, now),
            )
            conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now, case_id))
            document_id = int(cursor.lastrowid)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return {
        "document_id": document_id, "category": category, "filename": safe_name,
        "content_type": content_type, "size_bytes": len(contents), "policy_id": policy_id,
        "uploaded_at": now,
    }


@with_db_retry
def get_case_document_path(case_id: int, document_id: int) -> tuple[Path, str] | None:
    init_case_db()
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT stored_filename, original_filename FROM case_documents WHERE id = ? AND case_id = ?",
            (document_id, case_id),
        ).fetchone()
    if not row:
        return None
    path = (DATA_DIR / "cases" / str(case_id) / row[0]).resolve()
    if DATA_DIR not in path.parents or not path.is_file():
        return None
    return path, row[1]

