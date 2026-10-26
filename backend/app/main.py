from contextlib import asynccontextmanager
from pathlib import Path
import re
import uuid
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.ai import OllamaError, generate, select_relevant_chunks
from app.config import settings
from app.database import Base, engine, get_db
from app.extractors import SUPPORTED, extract_text
from app.models import Document
from app.schemas import AskRequest, AskResponse, DocumentDetail, DocumentOut, SummaryResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    yield

app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name)[:180] or "upload"

@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}

@app.get("/api/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()

@app.post("/api/documents", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    original = file.filename or "upload"
    suffix = Path(original).suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(415, f"Unsupported file type. Supported: {', '.join(sorted(SUPPORTED))}")
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit.")
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    upload_dir = Path(settings.upload_dir).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    path = upload_dir / stored_name
    path.write_bytes(data)
    try:
        text, _pages = extract_text(path)
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(422, f"Could not parse this document: {exc}") from exc
    doc = Document(
        filename=Path(original).name[:255],
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
        storage_path=str(path),
        extracted_text=text,
        status="processed" if text else "needs_ocr",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@app.get("/api/documents/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    return doc

@app.delete("/api/documents/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    Path(doc.storage_path).unlink(missing_ok=True)
    db.delete(doc)
    db.commit()
    return None

@app.post("/api/documents/{document_id}/ask", response_model=AskResponse)
async def ask_document(document_id: int, request: AskRequest, db: Session = Depends(get_db)):
    question = request.question.strip()
    if not question:
        raise HTTPException(422, "Question cannot be empty.")
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    if not doc.extracted_text.strip():
        raise HTTPException(422, "No text was extracted. This file may require OCR, which is not yet enabled in Phase 1.")
    chunks = select_relevant_chunks(doc.extracted_text, question)
    context = "\n\n".join(f"[Source {i+1}] {chunk}" for i, chunk in enumerate(chunks))
    prompt = (
        f"Document filename: {doc.filename}\n"
        f"Question: {question}\n\n"
        f"Source material:\n{context}\n\n"
        "Answer clearly using the source material. When useful, cite source labels like [Source 1]. "
        "If the source material is insufficient, say that explicitly."
    )
    try:
        answer = await generate(prompt)
    except OllamaError as exc:
        raise HTTPException(503, str(exc)) from exc
    citations = [{"source": f"Source {i+1}", "excerpt": chunk[:500]} for i, chunk in enumerate(chunks)]
    return {"answer": answer, "citations": citations}

@app.post("/api/documents/{document_id}/summarize", response_model=SummaryResponse)
async def summarize_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    if not doc.extracted_text.strip():
        raise HTTPException(422, "No text was extracted. OCR is not enabled in Phase 1.")
    # Bound the prompt to avoid sending arbitrarily large documents in a single request.
    text = doc.extracted_text[:24000]
    prompt = (
        f"Summarize the following document titled {doc.filename}. Provide: a concise overview, "
        "key points, important terms or findings, and any limitations visible in the text. "
        "Do not invent details. If the supplied text is truncated, state that the summary covers an excerpt.\n\n"
        f"Document text:\n{text}"
    )
    try:
        summary = await generate(prompt)
    except OllamaError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"summary": summary}
