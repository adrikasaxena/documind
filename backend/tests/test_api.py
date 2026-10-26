import os
from pathlib import Path
from fastapi.testclient import TestClient

# Configure isolated SQLite and uploads before importing the app.
os.environ["DATABASE_URL"] = "sqlite:///./test_documind.db"
os.environ["UPLOAD_DIR"] = "./test_uploads"
from app.main import app
from app.database import Base, engine

def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    Path("./test_uploads").mkdir(exist_ok=True)

def teardown_function():
    Base.metadata.drop_all(bind=engine)
    import shutil
    shutil.rmtree("./test_uploads", ignore_errors=True)

def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_upload_get_delete_txt():
    with TestClient(app) as client:
        response = client.post(
            "/api/documents",
            files={"file": ("notes.txt", b"hello document intelligence", "text/plain")},
        )
        assert response.status_code == 201, response.text
        document_id = response.json()["id"]
        detail = client.get(f"/api/documents/{document_id}")
        assert detail.status_code == 200
        assert "document intelligence" in detail.json()["extracted_text"]
        deleted = client.delete(f"/api/documents/{document_id}")
        assert deleted.status_code == 204
        assert client.get(f"/api/documents/{document_id}").status_code == 404

def test_reject_unsupported_type():
    with TestClient(app) as client:
        response = client.post(
            "/api/documents",
            files={"file": ("data.csv", b"a,b", "text/csv")},
        )
        assert response.status_code == 415
