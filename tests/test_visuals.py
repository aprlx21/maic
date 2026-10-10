import io
from types import SimpleNamespace

import pytest
from PIL import Image

from app.config import settings
from app.generation import create_design, demo_lesson
from app.schemas import Draft, LessonRequest, Slide, SlideContentPlan, VisualPlan
from app.storage import Storage
from app.visuals import download, image_bytes, prepare_media
from tests.conftest import upload
from tests.test_document import store_pdf


@pytest.fixture
def visual_job(client, pdf_bytes):
    from app.document import read_document
    source, _ = read_document(*store_pdf(pdf_bytes))
    request = LessonRequest(subject="Water", audience="Grade 6", duration_minutes=30, slide_count=3, image_mode="mixed")
    lesson = demo_lesson(request, source)
    content = SlideContentPlan(narrative="Observe then explain", omitted_source_ids=[], slides=[
        Slide(id=f"s{i}", title=f"Water {i}", takeaway="Observe water", bullets=["Observe", "Explain"],
              activity_id=lesson.activities[0].id, evidence_ids=[source.units[0].id],
              visual=VisualPlan(kind="photo", query=f"water leaf {i}", brief=f"Water on leaf {i}", caption="Quan sát giọt nước"))
        for i in range(3)])
    return upload(client, pdf_bytes), request, Draft(lesson=lesson, slide_content=content, design=create_design(content))


def fake_asset(origin):
    output = io.BytesIO()
    Image.new("RGB", (512, 512), "green").save(output, "JPEG")
    return output.getvalue(), {"origin": origin, "author": "Test", "license": "CC0", "title": "Leaf",
                               "source_url": "https://commons.wikimedia.org/wiki/File:Leaf.jpg" if origin == "internet" else ""}


def test_image_budget_cache_and_demo_do_not_make_extra_calls(visual_job, monkeypatch):
    job, request, draft = visual_job
    calls = []
    def internet(query):
        calls.append(query)
        return fake_asset("internet")
    monkeypatch.setattr("app.visuals.internet_image", internet)
    settings().max_slide_images = 2
    assert not any(m.get("asset_key") for m in prepare_media(job, request, draft, "demo").values())
    assert calls == []
    first = prepare_media(job, request, draft, "openai")
    assert len(calls) == 2
    assert first["s2"]["origin"] == "none"
    assert prepare_media(job, request, draft, "openai") == first
    assert len(calls) == 2


def test_failed_image_generation_is_counted_across_revisions(visual_job, monkeypatch):
    job, request, draft = visual_job
    request.image_mode = "ai"
    settings().max_ai_images = 1
    calls = []
    def unavailable(job_id, brief):
        calls.append(brief)
        raise RuntimeError("Provider unavailable")
    monkeypatch.setattr("app.visuals.generate_image", unavailable)
    assert all(m["origin"] == "none" for m in prepare_media(job, request, draft, "openai").values())
    draft.slide_content.slides[0].visual.brief = "A changed request"
    prepare_media(job, request, draft, "openai")
    assert len(calls) == 1
    ledger = Storage().get_json(f"jobs/{job}/image-attempts.json")
    assert len(ledger) == 1 and next(iter(ledger.values()))["status"] == "failed"


def test_internet_failure_falls_back_to_ai_and_labels_it(visual_job, monkeypatch):
    job, request, draft = visual_job
    settings().max_ai_images = 1
    monkeypatch.setattr("app.visuals.internet_image", lambda query: (_ for _ in ()).throw(ValueError("No results")))
    monkeypatch.setattr("app.visuals.generate_image", lambda job, brief: fake_asset("ai"))
    media = prepare_media(job, request, draft, "openai")
    assert media["s0"]["origin"] == "ai"
    assert Storage().exists(media["s0"]["asset_key"])
    assert media["s1"]["origin"] == "none"


def test_source_only_makes_no_network_calls(visual_job, monkeypatch):
    job, request, draft = visual_job
    request.image_mode = "source"
    def unexpected(*args):
        pytest.fail("Source-only mode must not call image providers")
    monkeypatch.setattr("app.visuals.internet_image", unexpected)
    monkeypatch.setattr("app.visuals.generate_image", unexpected)
    assert prepare_media(job, request, draft, "openai") == {}


@pytest.mark.parametrize("url", ["http://upload.wikimedia.org/a", "https://127.0.0.1/a",
                                  "https://upload.wikimedia.org.evil.test/a", "https://user@upload.wikimedia.org/a"])
def test_remote_download_rejects_untrusted_destinations(url):
    with pytest.raises(ValueError):
        download(url, "upload.wikimedia.org")


def test_image_decode_rejects_invalid_or_tiny_images():
    with pytest.raises(OSError):
        image_bytes(b"not an image")
    raw = io.BytesIO()
    Image.new("RGB", (20, 20)).save(raw, "PNG")
    with pytest.raises(ValueError):
        image_bytes(raw.getvalue())


def test_ai_adapter_uses_bounded_request_and_retains_usage(monkeypatch):
    import base64

    from app.visuals import generate_image
    calls = []
    def generate(**kwargs):
        calls.append(kwargs)
        raw, _ = fake_asset("ai")
        return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(raw).decode())],
                               usage=SimpleNamespace(model_dump=lambda: {"total_tokens": 321}))
    monkeypatch.setattr("app.visuals.openai_api_key", lambda: "test-key")
    monkeypatch.setattr("app.visuals.OpenAI", lambda **kwargs: SimpleNamespace(images=SimpleNamespace(generate=generate)))
    raw, meta = generate_image("test", "A glass with droplets")
    assert raw and calls[0]["n"] == 1 and calls[0]["quality"] == "low"
    assert calls[0]["size"] == "1024x1024"
    assert meta["origin"] == "ai" and meta["usage"]["total_tokens"] == 321
