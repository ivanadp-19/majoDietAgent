from typing import Optional
from uuid import uuid4

from src.db.supabase_client import get_supabase_client


def create_job(source_file: str) -> str:
    supabase = get_supabase_client()
    job_id = str(uuid4())
    supabase.table("ingestion_jobs").insert(
        {"id": job_id, "status": "queued", "source_file": source_file}
    ).execute()
    return job_id


def update_job(job_id: str, status: str, summary: Optional[str] = None, error: Optional[str] = None) -> None:
    supabase = get_supabase_client()
    payload = {"status": status}
    if summary is not None:
        payload["summary"] = summary
    if error is not None:
        payload["error"] = error
    supabase.table("ingestion_jobs").update(payload).eq("id", job_id).execute()


def get_job(job_id: str) -> Optional[dict]:
    supabase = get_supabase_client()
    result = supabase.table("ingestion_jobs").select("*").eq("id", job_id).limit(1).execute()
    return result.data[0] if result.data else None
