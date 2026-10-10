import hashlib
import io

import pymupdf as fitz
from PIL import Image

from app.document import read_document
from app.storage import Storage


def store_pdf(data):
    identity = hashlib.sha256(data).hexdigest()
    key = f"sources/{identity}/original.pdf"
    Storage().put(key, data)
    return key, identity


def test_page_evidence_markdown_and_cache(client, pdf_bytes):
    key, identity = store_pdf(pdf_bytes)
    source, cached = read_document(key, identity)
    assert not cached
    assert len(source.pages) == 3
    assert {u.page for u in source.units} == {1, 2, 3}
    assert len({u.id for u in source.units}) == len(source.units)
    for page in source.pages:
        markdown = Storage().get(page.markdown_key).decode()
        assert all(f"evidence:{uid} page:{page.page_no}" in markdown for uid in page.unit_ids)
    again, cached = read_document(key, identity)
    assert cached and again == source


def test_mixed_pdf_ocr_only_missing_text_pages(client, pdf_bytes, monkeypatch):
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    image = io.BytesIO()
    Image.new("RGB", (300, 300), "white").save(image, format="PNG")
    document.new_page().insert_image(fitz.Rect(20, 20, 320, 320), stream=image.getvalue())
    calls = []
    def unavailable_ocr(page, **kwargs):
        calls.append(page.number)
        raise RuntimeError("OCR unavailable in this isolated test")
    monkeypatch.setattr(fitz.Page, "get_textpage_ocr", unavailable_ocr)
    source, _ = read_document(*store_pdf(document.tobytes()))
    assert calls == [3]
    assert source.pages[3].status == "needs_review"
    assert all(p.status == "text" for p in source.pages[:3])
    assert any(u.asset_key for u in source.units if u.page == 4)


def test_ocr_failure_stops_before_generation(client, pdf_bytes, monkeypatch):
    from app.worker import run_once
    from tests.conftest import upload
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    image = document[0].get_pixmap().tobytes("png")
    scan = fitz.open()
    scan.new_page().insert_image(fitz.Rect(0, 0, 595, 842), stream=image)
    def unavailable(*args, **kwargs):
        raise RuntimeError("OCR unavailable")
    monkeypatch.setattr(fitz.Page, "get_textpage_ocr", unavailable)
    job_id = upload(client, scan.tobytes())
    run_once()
    detail = client.get(f"/api/jobs/{job_id}").json()
    assert detail["status"] == "failed"
    assert "OCR" in detail["error"]
    assert not detail["usage"]


def test_cache_changes_with_ocr_data(client, pdf_bytes, tmp_path):
    from app.config import settings
    key, identity = store_pdf(pdf_bytes)
    before, _ = read_document(key, identity)
    settings().tessdata_prefix = str(tmp_path / "tessdata")
    (tmp_path / "tessdata").mkdir()
    (tmp_path / "tessdata/eng.traineddata").write_bytes(b"test-model-identity")
    after, cached = read_document(key, identity)
    assert not cached and before.parser_version != after.parser_version
    assert Storage().exists(before.pages[0].markdown_key)


def test_real_ocr_scan(client, pdf_bytes):
    from pathlib import Path

    import pytest

    from app.config import ROOT, settings
    data = ROOT / "data/tessdata"
    if not all((data / f"{lang}.traineddata").exists() for lang in ("vie", "eng")):
        pytest.skip("OCR language data not installed")
    settings().tessdata_prefix = str(Path(data))
    original = fitz.open(stream=pdf_bytes, filetype="pdf")
    scan = fitz.open()
    scan.new_page().insert_image(original[0].rect, stream=original[0].get_pixmap(matrix=fitz.Matrix(2, 2)).tobytes("png"))
    result, _ = read_document(*store_pdf(scan.tobytes()))
    assert result.pages[0].status == "ocr"
    assert "evaporation" in " ".join(u.content.lower() for u in result.units)
