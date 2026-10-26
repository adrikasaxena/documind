from pathlib import Path
from app.extractors import chunks_for_text, extract_text

def test_txt_extraction(tmp_path: Path):
    path = tmp_path / "sample.txt"
    path.write_text("A document about machine learning.", encoding="utf-8")
    text, pages = extract_text(path)
    assert "machine learning" in text
    assert pages[0]["page"] is None

def test_chunks_overlap_and_content():
    text = "alpha " * 1000
    chunks = chunks_for_text(text, max_chars=500, overlap=50)
    assert len(chunks) > 1
    assert all(chunks)

def test_unsupported_file(tmp_path: Path):
    path = tmp_path / "sample.csv"
    path.write_text("a,b", encoding="utf-8")
    try:
        extract_text(path)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Unsupported" in str(exc)
