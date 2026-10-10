import hashlib
import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy import select

from app.config import ROOT, settings
from app.db import Event, Job, Publication, Revision, Usage, init_db, new_id, now, session
from app.document import extraction_key, validate_pdf
from app.schemas import Decision, LessonRequest
from app.storage import Storage
from app.workflow import check_approval


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="MAIC Offline", version="0.1.0", lifespan=lifespan)


def get_job(db, job_id):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Không tìm thấy bài dạy")
    return job


def job_summary(job):
    return {"id": job.id, "filename": job.filename, "status": job.status, "request": job.request,
            "mode": job.mode, "current_revision": job.current_revision, "error": job.error,
            "created_at": job.created_at.isoformat() + "Z", "elapsed_seconds": job.elapsed_seconds,
            "processing": job.runnable}


def revision_json(revision):
    return {"id": revision.id, "number": revision.number, "draft": revision.draft,
            "approval_hash": revision.content_hash, "artifacts": revision.artifacts,
            "reviews": revision.reviews, "created_at": revision.created_at.isoformat() + "Z"}


@app.get("/api/health")
def health():
    with session() as db:
        db.execute(select(1))
    return {"status": "ok"}


@app.get("/api/config")
def config():
    cfg = settings()
    return {"mode": cfg.mode, "model": cfg.model, "max_pdf_mb": cfg.max_pdf_mb,
            "max_pages": cfg.max_pages, "max_slides": cfg.max_slides,
            "max_ai_images": cfg.max_ai_images, "max_slide_images": cfg.max_slide_images,
            "trusted_group_only": True, "cost_rates_configured": cfg.input_usd_per_million is not None}


@app.post("/api/jobs", status_code=201)
async def upload(file: Annotated[UploadFile, File()], request: Annotated[str, Form()]):
    cfg = settings()
    try:
        spec = LessonRequest.model_validate_json(request)
    except ValidationError as exc:
        raise HTTPException(422, str(exc)) from exc
    if spec.slide_count > cfg.max_slides:
        raise HTTPException(422, f"Tối đa {cfg.max_slides} slide")
    buffer = bytearray()
    while chunk := await file.read(1024 * 1024):
        buffer.extend(chunk)
        if len(buffer) > cfg.max_pdf_mb * 1024 * 1024:
            raise HTTPException(413, f"PDF vượt quá {cfg.max_pdf_mb} MB")
    data = bytes(buffer)
    try:
        validate_pdf(data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    source_hash = hashlib.sha256(data).hexdigest()
    source_key = f"sources/{source_hash}/original.pdf"
    Storage().put(source_key, data, "application/pdf")
    with session() as db:
        job = Job(filename=Path(file.filename or "document.pdf").name[:255], source_hash=source_hash,
                  source_key=source_key, request=spec.model_dump(), mode=cfg.mode)
        db.add(job)
        db.flush()
        db.add(Event(job_id=job.id, stage="queued", message="Đã nhận PDF, chờ xử lý", details={}))
        return job_summary(job)


@app.get("/api/jobs")
def list_jobs():
    with session() as db:
        return [job_summary(j) for j in db.scalars(select(Job).order_by(Job.created_at.desc()).limit(100))]


@app.get("/api/jobs/{job_id}")
def detail(job_id: str):
    storage = Storage()
    with session() as db:
        job = get_job(db, job_id)
        revision = db.get(Revision, job.current_revision) if job.current_revision else None
        revisions = list(db.scalars(select(Revision).where(Revision.job_id == job_id).order_by(Revision.number)))
        usages = list(db.scalars(select(Usage).where(Usage.job_id == job_id)))
        events = list(db.scalars(select(Event).where(Event.job_id == job_id).order_by(Event.id)))
        pubs = list(db.scalars(select(Publication).where(Publication.job_id == job_id).order_by(Publication.version)))
        result = {**job_summary(job), "source_key": job.source_key,
                  "revision": revision_json(revision) if revision else None,
                  "revisions": [{"id": r.id, "number": r.number, "approval_hash": r.content_hash} for r in revisions],
                  "usage": [{"stage": u.stage, "model": u.model, "input_tokens": u.input_tokens,
                             "output_tokens": u.output_tokens, "cached_tokens": u.cached_tokens,
                             "full_context_tokens": u.full_context_tokens, "selected_context_tokens": u.selected_context_tokens,
                             "seconds": u.seconds, "cost_usd": u.cost_usd, "status": u.status} for u in usages],
                  "events": [{"id": e.id, "stage": e.stage, "message": e.message, "details": e.details,
                              "created_at": e.created_at.isoformat() + "Z"} for e in events],
                  "publications": [{"version": p.version, "revision_id": p.revision_id, "approval_hash": p.approval_hash,
                                    "teacher_name": p.teacher_name, "artifacts": p.artifacts,
                                    "package_key": p.package_key} for p in pubs]}
        key = f"jobs/{job.id}/source.json"
        if not storage.exists(key):
            key = extraction_key(job.source_hash)
        result["source"] = storage.get_json(key) if storage.exists(key) else None
        images_key = f"jobs/{job.id}/image-attempts.json"
        attempts = storage.get_json(images_key).values() if storage.exists(images_key) else []
        result["image_usage"] = {"ai_attempts": sum(a["provider"] == "ai" for a in attempts),
                                 "internet_searches": sum(a["provider"] == "internet" for a in attempts)}
        return result


@app.get("/api/jobs/{job_id}/revisions/{revision_id}")
def get_revision(job_id: str, revision_id: str):
    with session() as db:
        get_job(db, job_id)
        revision = db.get(Revision, revision_id)
        if not revision or revision.job_id != job_id:
            raise HTTPException(404, "Không tìm thấy revision")
        return revision_json(revision)


@app.post("/api/jobs/{job_id}/decisions", status_code=202)
def decide(job_id: str, decision: Decision):
    with session() as db:
        job = db.get(Job, job_id, with_for_update=True)
        if not job:
            raise HTTPException(404, "Không tìm thấy bài dạy")
        # Atomic state transition works for both PostgreSQL and local SQLite.
        if job.status not in {"awaiting_teacher", "published"} or job.runnable:
            raise HTTPException(409, "Bài dạy đang xử lý hoặc chưa sẵn sàng duyệt")
        if job.status == "published" and decision.action not in {"edit", "request_revision"}:
            raise HTTPException(409, "Bản này đã phát hành; hãy tạo revision mới để chỉnh sửa")
        revision = db.get(Revision, job.current_revision)
        if not revision or revision.id != decision.revision_id or revision.content_hash != decision.approval_hash:
            raise HTTPException(409, "Revision đã thay đổi, hãy tải lại trước khi gửi quyết định")
        if decision.action == "edit" and decision.draft is None:
            raise HTTPException(422, "Chỉnh sửa cần có dữ liệu bản nháp")
        if decision.action == "request_revision" and not decision.feedback.strip():
            raise HTTPException(422, "Hãy nhập yêu cầu sửa")
        if decision.draft and len(decision.draft.slide_content.slides) > settings().max_slides:
            raise HTTPException(422, "Số slide vượt giới hạn")
        try:
            if decision.action == "approve":
                check_approval(revision, decision)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        from sqlalchemy import update
        result = db.execute(update(Job).where(Job.id == job_id, Job.runnable.is_(False), Job.current_revision == revision.id,
                                             Job.status == job.status).values(
            status="queued", runnable=True, pending_command={"id": new_id(), "decision": decision.model_dump()}, updated_at=now()))
        if result.rowcount != 1:
            raise HTTPException(409, "Một quyết định khác vừa được gửi; hãy tải lại")
        db.add(Event(job_id=job_id, stage="teacher_decision", message=f"{decision.teacher_name}: {decision.action}",
                     details=decision.model_dump(exclude={"draft"})))
    return {"queued": True}


@app.post("/api/jobs/{job_id}/retry", status_code=202)
def retry(job_id: str):
    with session() as db:
        job = get_job(db, job_id)
        if job.status != "failed" or job.runnable:
            raise HTTPException(409, "Chỉ có thể thử lại job bị lỗi")
        job.status = "queued"
        job.runnable = True
        job.error = None
        job.updated_at = now()
    return {"queued": True}


@app.get("/api/jobs/{job_id}/asset")
def asset(job_id: str, key: str, download: bool = False):
    storage = Storage()
    with session() as db:
        job = get_job(db, job_id)
        allowed = {job.source_key}
        for r in db.scalars(select(Revision).where(Revision.job_id == job_id)):
            allowed.update(r.artifacts["files"].values())
        for p in db.scalars(select(Publication).where(Publication.job_id == job_id)):
            allowed.update(p.artifacts.values())
            allowed.add(p.package_key)
        extracted_key = f"jobs/{job.id}/source.json"
        if not storage.exists(extracted_key):
            extracted_key = extraction_key(job.source_hash)
        if storage.exists(extracted_key):
            source = storage.get_json(extracted_key)
            for page in source["pages"]:
                allowed.update((page["markdown_key"], page["preview_key"]))
            allowed.update(u["asset_key"] for u in source["units"] if u["asset_key"])
        if key not in allowed:
            raise HTTPException(404, "Không tìm thấy tài nguyên của bài dạy")
    try:
        storage.get(key)
    except FileNotFoundError as exc:
        raise HTTPException(404, "File chưa sẵn sàng") from exc
    return FileResponse(storage.path(key), media_type=mimetypes.guess_type(key)[0] or "application/octet-stream",
                        filename=Path(key).name if download else None,
                        headers={"X-Content-Type-Options": "nosniff"})


@app.get("/api/lessons/{lesson_id}/versions/{version}")
def published_package(lesson_id: str, version: int):
    with session() as db:
        publication = db.scalar(select(Publication).where(Publication.job_id == lesson_id, Publication.version == version))
        if not publication:
            raise HTTPException(404, "Phiên bản chưa được phát hành")
        return Storage().get_json(publication.package_key)


@app.get("/api/sample.pdf")
def sample_pdf():
    import pymupdf as fitz
    document = fitz.open()
    texts = [
        ("The water cycle", "Water moves through evaporation, condensation and precipitation. The Sun provides energy for evaporation. Water vapour cools and condenses to form clouds."),
        ("Observe and explain", "Evaporation changes liquid water into vapour. Condensation changes vapour into liquid droplets. Precipitation returns water to the surface as rain or snow."),
        ("Apply your knowledge", "Compare a wet cloth drying in sunlight and in shade. Explain the difference using evaporation. Draw a diagram connecting evaporation, condensation and precipitation.")]
    for title, body in texts:
        page = document.new_page()
        page.insert_text((50, 65), title, fontsize=22)
        page.insert_textbox(fitz.Rect(50, 100, 540, 350), body, fontsize=14)
    data = document.tobytes()
    document.close()
    return Response(data, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=water-cycle.pdf"})


static = ROOT / "frontend/dist"
if static.exists():
    app.mount("/", StaticFiles(directory=static, html=True), name="frontend")
