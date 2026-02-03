import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from src.api.schemas import IngestResponse, JobStatusResponse
from src.db.jobs import create_job, get_job, update_job
from src.utils.document_loader import load_document_text
from src.workflows.extraction import meal_extraction_workflow

router = APIRouter()


def _run_ingestion(job_id: str, file_path: str) -> None:
    update_job(job_id, "processing")
    temp_path = Path(file_path)
    try:
        document_text = load_document_text(file_path)
        run_output = meal_extraction_workflow.run(
            input=document_text,
            additional_data={"file_path": file_path},
        )
        update_job(job_id, "completed", summary=str(run_output.content))
    except Exception as exc:
        update_job(job_id, "failed", error=str(exc))
    finally:
        if temp_path.exists():
            temp_path.unlink()


@router.post("", response_model=IngestResponse, status_code=202)
def ingest_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> IngestResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(file.file.read())

    job_id = create_job(source_file=tmp_path.name)
    background_tasks.add_task(_run_ingestion, job_id, str(tmp_path))
    return IngestResponse(job_id=job_id, status="queued")


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job["id"],
        status=job["status"],
        summary=job.get("summary"),
        error=job.get("error"),
    )
