# DocuMind AI — Phase 1

A local-first AI document intelligence project. This phase implements a real vertical slice:
- FastAPI backend with SQLite by default and PostgreSQL support through `DATABASE_URL`
- Upload/list/get/delete documents
- Extract text from PDF, DOCX, and TXT
- Persist document text and status
- Ask questions against uploaded document text using local Ollama inference
- Generate summaries with a local Ollama model
- React + TypeScript frontend for upload, library, preview, chat, and summaries
- Backend tests for document extraction/API behavior

No hosted AI API is used. AI features require a local Ollama server and downloaded model.

## Requirements

- macOS
- Python 3.11 or 3.12 recommended
- Node.js 20+ and npm
- Ollama
- For OCR of image-only PDFs and image files, install Tesseract separately; OCR support is a later phase in this starter.
- Free disk space: at least 8–12 GB for dependencies and a small model.

## 1. Check your Mac

Run in Terminal:

```bash
uname -m
python3 --version
node --version
npm --version
```

`arm64` means Apple Silicon; `x86_64` means Intel. Also check Apple menu → About This Mac for memory and chip.

## 2. Install Ollama and a model

Install Ollama from https://ollama.com/download/mac, open it, then:

```bash
ollama --version
ollama pull qwen3.5:2b
ollama pull nomic-embed-text
ollama run qwen3.5:2b
```

Type a short prompt to verify it works, then exit with `/bye`. The app uses `qwen3.5:2b` by default. If your Mac has 16 GB unified memory, you can try `qwen3.5:4b`; 24 GB or more may allow `qwen3.5:9b`, depending on other apps and context size. Model sizes and performance change; use `ollama list` to verify installed models. The embedding model is reserved for a later semantic-search phase.

Official model library: https://ollama.com/library/qwen3.5

## 3. Start the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open http://127.0.0.1:8000/docs for interactive API documentation.

SQLite is used by default so the project starts without installing PostgreSQL. To use PostgreSQL, create a database and set `DATABASE_URL` in `backend/.env`, for example:

```env
DATABASE_URL=postgresql+psycopg://documind:your_password@localhost:5432/documind
```

Then install/run PostgreSQL and restart the backend. Production-grade migrations and ownership-aware accounts are scheduled for a later phase.

## 4. Start the frontend

In a second Terminal window:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open the local URL printed by Vite (usually http://localhost:5173).

## 5. Run tests

In the backend virtual environment:

```bash
cd backend
pytest -q
```

Tests that do not require Ollama run without a model. AI endpoints require Ollama to be running and the configured model to be downloaded.

## Current phase scope and limitations

This is the tested Phase 1 foundation, not a claim that every planned feature is already implemented. It currently supports PDF text-layer extraction, DOCX, and TXT. Scanned-page OCR, image understanding, authentication, pgvector semantic search, multi-document chat, comparison, structured extraction, exports, and deployment hardening are planned for subsequent phases. The chat uses retrieved text chunks and displays page numbers where available. It should not be treated as a source of legal, medical, or financial advice.
