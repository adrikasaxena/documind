from pathlib import Path
import fitz
from docx import Document as DocxDocument

SUPPORTED = {".pdf", ".docx", ".txt"}

def extract_text(path: Path) -> tuple[str, list[dict]]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        pages = []
        with fitz.open(path) as pdf:
            for index, page in enumerate(pdf):
                text = page.get_text("text").strip()
                if text:
                    pages.append({"page": index + 1, "text": text})
        return "\n\n".join(p["text"] for p in pages), pages
    if suffix == ".docx":
        doc = DocxDocument(path)
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return text, [{"page": None, "text": text}] if text else []
    if suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        return text, [{"page": None, "text": text}] if text else []
    raise ValueError(f"Unsupported file type: {suffix}")

def chunks_for_text(text: str, max_chars: int = 1800, overlap: int = 250) -> list[str]:
    clean = text.strip()
    if not clean:
        return []
    chunks, start = [], 0
    while start < len(clean):
        end = min(len(clean), start + max_chars)
        if end < len(clean):
            boundary = clean.rfind(" ", start + max_chars // 2, end)
            if boundary > start:
                end = boundary
        chunks.append(clean[start:end].strip())
        if end >= len(clean):
            break
        start = max(start + 1, end - overlap)
    return [chunk for chunk in chunks if chunk]
