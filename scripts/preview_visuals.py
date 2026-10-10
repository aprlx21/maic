"""Render the local visual fixture with the real slide adapter; no model calls."""
import hashlib
import json
from pathlib import Path

from app.config import settings
from app.document import read_document
from app.generation import create_design, demo_lesson
from app.main import sample_pdf
from app.rendering import build_deck
from app.schemas import Draft, LessonRequest, Slide, SlideContentPlan, VisualPlan
from app.storage import Storage


def main():
    root = Path(__file__).resolve().parents[1] / "data/visual-preview"
    storage = Storage()
    data = sample_pdf().body
    identity = hashlib.sha256(data).hexdigest()
    source, _ = read_document(storage.put(f"sources/{identity}/original.pdf", data), identity)
    request = LessonRequest(subject="Chu trình nước", audience="Lớp 6", duration_minutes=30, slide_count=4)
    lesson = demo_lesson(request, source)
    evidence = [next(u.id for u in source.units if u.kind == "paragraph")]
    slides = []
    content = [
        ("Quan sát giọt nước trên lá", "Từ một hình ảnh đời thường, đặt câu hỏi khoa học.",
         ["Giọt nước có hình dạng và vị trí như thế nào?", "Ảnh cho thấy điều gì? Điều gì cần kiểm chứng thêm?"],
         "photo", "Ảnh thực tế: giọt nước trên lá", ""),
        ("Vì sao bên ngoài cốc lạnh có nước?", "Liên hệ ngưng tụ với một đồ vật quen thuộc.",
         ["Quan sát những giọt nước ở thành ngoài cốc.", "Vận dụng kiến thức về hơi nước và ngưng tụ để giải thích."],
         "illustration", "Cốc nước lạnh — minh họa AI", ""),
        ("Kết nối ba quá trình", "Nước chuyển động qua các giai đoạn của chu trình.",
         ["Bay hơi: nước lỏng chuyển thành hơi nước.", "Ngưng tụ: hơi nước tạo thành giọt nước.", "Giáng thủy: nước trở lại bề mặt."],
         "process", "", ""),
        ("Thử giải thích trong đời sống", "Dùng nguyên lý trong tài liệu để đưa ra dự đoán.",
         ["Dự đoán điều kiện làm khăn khô nhanh hơn.", "Đề xuất cách quan sát để kiểm tra dự đoán."],
         "process", "", "Tình huống giả định: Hai khăn ướt giống nhau được phơi ở chỗ nắng và chỗ râm. Em dự đoán điều gì?"),
    ]
    for i, (title, takeaway, bullets, kind, caption, example) in enumerate(content):
        slides.append(Slide(id=f"s{i+1}", title=title, takeaway=takeaway, bullets=bullets,
                            activity_id=lesson.activities[0].id, evidence_ids=evidence,
                            visual=VisualPlan(kind=kind, caption=caption), practical_example=example))
    plan = SlideContentPlan(narrative="Quan sát → giải thích → mô hình hóa → vận dụng", slides=slides, omitted_source_ids=[])
    draft = Draft(lesson=lesson, slide_content=plan, design=create_design(plan))
    media = {}
    for sid, filename, metadata in [
        ("s1", "internet-photo.jpg", json.loads((root / "internet-photo.json").read_text(encoding="utf-8"))),
        ("s2", "ai-condensation.png", {"origin": "ai", "title": "Cốc lạnh và các giọt ngưng tụ",
                                      "author": "ImageGen", "license": "AI-generated illustration", "source_url": ""}),
    ]:
        raw = (root / filename).read_bytes()
        media[sid] = {**metadata, "asset_key": storage.put(f"visual-preview/{filename}", raw),
                      "sha256": hashlib.sha256(raw).hexdigest(), "caption": slides[int(sid[1:])-1].visual.caption}
    settings().slide_font = "Arial"
    report = build_deck(draft, source, root / "deck", "demo", media)
    (root / "deck/geometry.json").write_text(json.dumps(report), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
