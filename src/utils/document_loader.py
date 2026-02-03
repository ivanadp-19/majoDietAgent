from pathlib import Path

from pypdf import PdfReader


def load_document_text(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf_text(path)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")

    raise ValueError(f"Unsupported file type: {suffix}")


def _load_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages_text.append(page_text)
    return "\n".join(pages_text)
