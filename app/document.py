import hashlib
import os
from collections import Counter
from pathlib import Path

import pymupdf as fitz
from filelock import FileLock

from app.config import settings
from app.schemas import ContentUnit, PageRecord, SourceDocument
from app.storage import Storage

PARSER_VERSION = "page-units-v2"


def parser_version():
    cfg = settings()
    root = cfg.tessdata_prefix or os.environ.get("TESSDATA_PREFIX", "")
    stamp = hashlib.sha256(cfg.ocr_languages.encode())
    for lang in cfg.ocr_languages.split("+"):
        path = Path(root) / f"{lang}.traineddata"
        stamp.update(path.read_bytes() if root and path.is_file() else b"unavailable")
    return f"{PARSER_VERSION}-{stamp.hexdigest()[:12]}"


def validate_pdf(data: bytes):
    cfg = settings()
    if len(data) > cfg.max_pdf_mb * 1024 * 1024:
        raise ValueError(f"PDF vượt quá {cfg.max_pdf_mb} MB")
    if not data.startswith(b"%PDF-"):
        raise ValueError("Chỉ chấp nhận file PDF hợp lệ")
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            if doc.needs_pass:
                raise ValueError("PDF được bảo vệ bằng mật khẩu")
            if not 1 <= len(doc) <= cfg.max_pages:
                raise ValueError(f"PDF cần có từ 1 đến {cfg.max_pages} trang")
            for page in doc:
                page.get_text()
    except (fitz.FileDataError, RuntimeError) as exc:
        raise ValueError("Không đọc được PDF") from exc


def extraction_key(document_id):
    return f"sources/{document_id}/{parser_version()}/document.json"


def read_document(source_key: str, document_id: str):
    storage = Storage()
    cache = extraction_key(document_id)
    lock = settings().data_dir / f"extract-{document_id}.lock"
    with FileLock(str(lock)):
        if storage.exists(cache):
            return SourceDocument.model_validate(storage.get_json(cache)), True
        result = _extract(storage, source_key, document_id)
        storage.put_json(cache, result.model_dump())
        return result, False


def _extract(storage, source_key, document_id):
    cfg = settings()
    if cfg.tessdata_prefix:
        os.environ["TESSDATA_PREFIX"] = cfg.tessdata_prefix
    version = parser_version()
    prefix = f"sources/{document_id}/{version}"
    pages, units, all_warnings = [], [], []
    with fitz.open(stream=storage.get(source_key), filetype="pdf") as doc:
        for index, page in enumerate(doc):
            page_no = index + 1
            page_units, warnings = [], []
            native = page.get_text("dict", sort=True)
            text_count = sum(len(s["text"].strip()) for b in native["blocks"] if b["type"] == 0
                             for line in b["lines"] for s in line["spans"])
            status = "text"
            has_visual = bool(page.get_images()) or bool(page.get_drawings())
            if text_count < 30 and has_visual:
                try:
                    tp = page.get_textpage_ocr(language=cfg.ocr_languages, dpi=200, full=True,
                                               tessdata=cfg.tessdata_prefix or None)
                    native = page.get_text("dict", textpage=tp, sort=True)
                    ocr_text = page.get_text(textpage=tp).strip()
                    status = "ocr" if len(ocr_text) >= 20 else "needs_review"
                    warnings.append("Nội dung OCR cần được đối chiếu với ảnh trang; công thức/bảng có thể sai.")
                except Exception as exc:  # noqa: BLE001 -- OCR backends expose several exception types; page is blocked.
                    status = "needs_review"
                    warnings.append(f"OCR chưa đọc được trang {page_no}: {type(exc).__name__}")
            elif text_count == 0:
                status = "blank"
            preview_key = f"{prefix}/pages/{page_no:03}.png"
            storage.put(preview_key, page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25)).tobytes("png"), "image/png")
            sizes = Counter(round(s["size"]) for b in native["blocks"] if b["type"] == 0
                            for line in b["lines"] for s in line["spans"])
            body_size = sizes.most_common(1)[0][0] if sizes else 11

            def add(kind, content, bbox, asset_key=None, page_no=page_no, page_units=page_units):
                uid = f"p{page_no:03}-u{len(page_units)+1:03}"
                page_units.append(ContentUnit(id=uid, page=page_no, kind=kind, content=content,
                                               bbox=list(bbox), asset_key=asset_key))

            table_rects = []
            if status == "text":
                try:
                    tables = page.find_tables()
                    for table in tables:
                        rows = table.extract()
                        if len(rows) > 1:
                            content = "\n".join(" | ".join(str(c or "").replace("\n", " ") for c in row) for row in rows)
                            add("table", content, table.bbox)
                            table_rects.append(fitz.Rect(table.bbox))
                except Exception:  # noqa: BLE001 -- preserve text and image if optional table recognition fails.
                    warnings.append("Không xác định được cấu trúc bảng; giữ lại văn bản và ảnh trang.")
            for block in native["blocks"]:
                if block["type"] != 0:
                    continue
                rect = fitz.Rect(block["bbox"])
                if any(t.contains(rect) for t in table_rects):
                    continue
                lines = [" ".join(s["text"] for s in line["spans"]).strip() for line in block["lines"]]
                content = "\n".join(lines).strip()
                if not content:
                    continue
                size = max(s["size"] for line in block["lines"] for s in line["spans"])
                kind = "ocr" if status in {"ocr", "needs_review"} else (
                    "heading" if size > body_size * 1.15 and len(content) < 180 else "paragraph")
                add(kind, content, block["bbox"])
            # Crop by position, preserving figure/page provenance (including inline raster images).
            image_blocks = page.get_text("dict")["blocks"]
            for block in image_blocks:
                if block["type"] != 1 or status in {"ocr", "needs_review"}:
                    continue
                if block["width"] < 40 or block["height"] < 40:
                    continue
                key = f"{prefix}/figures/p{page_no:03}-{len(page_units)+1:03}.png"
                storage.put(key, page.get_pixmap(clip=fitz.Rect(block["bbox"]), matrix=fitz.Matrix(2, 2)).tobytes("png"), "image/png")
                add("figure", f"Hình tại trang {page_no}; xem ảnh để diễn giải.", block["bbox"], key)
            # Vector diagrams are preserved in a page image; never silently discard visual evidence.
            if page.get_drawings() or status in {"ocr", "needs_review"}:
                add("figure", f"Ảnh trang {page_no}: dùng đối chiếu hình, bảng và công thức.", list(page.rect), preview_key)
            if not page_units and status != "blank":
                status = "needs_review"
                warnings.append("Không trích được nội dung trang.")
            markdown = f"# Trang {page_no}\n\n" + "\n\n".join(
                f"<!-- evidence:{u.id} page:{u.page} -->\n" +
                (f"![{u.content}]({u.asset_key})" if u.asset_key else u.content)
                for u in page_units)
            md_key = f"{prefix}/pages/{page_no:03}.md"
            storage.put(md_key, markdown.encode(), "text/markdown; charset=utf-8")
            pages.append(PageRecord(page_no=page_no, status=status, unit_ids=[u.id for u in page_units],
                                    markdown_key=md_key, preview_key=preview_key, warnings=warnings))
            units.extend(page_units)
            all_warnings.extend(warnings)
    if not units:
        raise ValueError("PDF không có nội dung có thể sử dụng")
    return SourceDocument(document_id=document_id, parser_version=version, source_key=source_key,
                          pages=pages, units=units, warnings=all_warnings)
