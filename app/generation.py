from PIL import Image, ImageOps

from app.config import settings
from app.context import select_context
from app.schemas import (
    Activity,
    CombinedReview,
    DesignPlan,
    Draft,
    Finding,
    LessonContent,
    LessonPlan,
    KnowledgeSection,
    Objective,
    Review,
    ScriptBatch,
    ScriptItem,
    Slide,
    SlideContentPlan,
    SlideDesign,
    TeachingScript,
    VisualPlan,
    digest,
)
from app.storage import Storage
from app.validation import grounded_review, validate_draft


def source_previews(source, context, evidence_ids=()):
    """Ground noisy OCR in the original page pixels, within a bounded image budget."""
    preferred = {u.page for u in source.units if u.id in evidence_ids}
    pages = [p for p in source.pages if p.status == "ocr"
             and (p.page_no in preferred or any(f"[{uid} |" in context for uid in p.unit_ids))]
    pages.sort(key=lambda p: (p.page_no not in preferred, p.page_no))
    storage = Storage()
    paths = []
    for page in pages[:6]:
        storage.get(page.preview_key)
        paths.append(storage.path(page.preview_key))
    return paths


def demo_lesson(request, source):
    content = [u for u in source.units if u.kind != "figure"] or source.units
    selected = [content[min(i, len(content)-1)] for i in range(3)]
    titles = ["Khởi động và kết nối", "Khám phá kiến thức", "Vận dụng và đánh giá"]
    times = [max(2, request.duration_minutes // 5), max(3, request.duration_minutes * 3 // 5)]
    times.append(request.duration_minutes - sum(times))
    objectives = [Objective(id=f"o{i+1}", text=f"Giải thích và vận dụng: {u.content[:100]}", evidence_ids=[u.id]) for i, u in enumerate(selected)]
    return LessonPlan(title=f"{request.subject} · Bài dạy minh họa", audience=request.audience,
                      objectives=objectives, prerequisites=["Đọc phần tài liệu được giao trước buổi học."],
                      materials=["PDF nguồn", "Bộ slide và phiếu học tập"],
                      activities=[Activity(id=f"a{i+1}", title=titles[i], minutes=times[i],
                                           teacher_action=f"Hướng dẫn đọc trang {u.page} và giải thích: {u.content[:250]}",
                                           learner_action="Đọc tài liệu, trao đổi theo cặp và trình bày điều đã hiểu.",
                                           assessment="Đối chiếu câu trả lời với nội dung trang nguồn.",
                                           objective_ids=[f"o{i+1}"], evidence_ids=[u.id]) for i, u in enumerate(selected)],
                      homework="Viết một đoạn tóm tắt các kiến thức đã học, ghi rõ trang nguồn.")


def require_sections(content):
    sections = content.sections
    if (not sections or len({k.id for k in sections}) != len(sections)
            or [sid for k in sections for sid in k.slide_ids] != [s.id for s in content.slides]):
        raise ValueError("Phân phần K thiếu, trùng hoặc sai thứ tự slide; mỗi slide phải thuộc đúng một phần.")


def create_draft(gen, request, source):
    context, full, selected = select_context(source, request.subject + " " + request.requirements,
                                             settings().context_tokens, mode=request.context_mode)
    def example():
        lesson = demo_lesson(request, source)
        units = {u.id: u for u in source.units}
        slides = []
        for i in range(request.slide_count):
            activity = lesson.activities[min(i * len(lesson.activities) // request.slide_count, len(lesson.activities)-1)]
            unit = units[activity.evidence_ids[0]]
            slides.append(Slide(id=f"s{i+1:03}", title=f"{activity.title} · {i+1}",
                                takeaway=unit.content[:140].replace("\n", " "),
                                bullets=[unit.content[:150].replace("\n", " "), "Đối chiếu ý chính với tài liệu nguồn."],
                                activity_id=activity.id, evidence_ids=[unit.id],
                                visual=VisualPlan(kind="process" if i % 3 == 1 else "photo",
                                    query=request.subject, brief=unit.content[:400], caption="Quan sát và giải thích")))
        used = {e for slide in slides for e in slide.evidence_ids}
        return LessonContent(lesson=lesson, slide_content=SlideContentPlan(
            narrative="Tiến trình từ nhận biết đến vận dụng, theo giáo án.", slides=slides,
            sections=[KnowledgeSection(id=f"k{i+1:03}", title=a.title,
                summary=a.teacher_action[:500], slide_ids=[s.id for s in slides if s.activity_id == a.id])
                for i, a in enumerate(lesson.activities) if any(s.activity_id == a.id for s in slides)],
            omitted_source_ids=[u.id for u in source.units if u.id not in used])).model_dump()
    result = gen.call("draft", LessonContent,
                      "Soạn giáo án và nội dung slide trong một lượt. Mục tiêu đo được; tổng phút hoạt động bằng yêu cầu. "
                      "Chia bộ slide thành các phần kiến thức K theo chủ đề (sections): mỗi phần có id k001..., "
                      "title, summary và slide_ids. Mỗi slide thuộc đúng một phần; các phần và slide_ids theo thứ tự "
                      "trình chiếu, mỗi phần gồm các slide liên tiếp. Chia theo nội dung kiến thức, không chỉ theo hoạt động. "
                      "Mỗi slide một thông điệp, mỗi bullet tối đa 180 ký tự. Đúng số slide, ID duy nhất và liên kết "
                      "activity_id/objective_ids/evidence_ids hợp lệ. teaching_script=null, omitted_source_ids=[]. "
                      "Chỉ chọn figure_id được liệt kê trong figures khi hình liên quan. Viết ngắn gọn, không lặp nguồn. "
                      "Thiết kế bài thiên về hình ảnh: khoảng 2/3 slide có hình hoặc sơ đồ hữu ích; không ép hình trang trí. "
                      "visual.kind=photo cho cảnh đời thường cụ thể, illustration cho khái niệm cần minh họa AI, "
                      "process chỉ khi các bullet thực sự là các bước có thứ tự (2-5 bước ngắn). "
                      "visual.query là 3-7 từ tiếng Anh để tìm ảnh đúng chủ thể; brief mô tả cảnh cụ thể, không chữ/nhãn; "
                      "caption tiếng Việt nêu điều cần quan sát, không khẳng định đó là sự kiện có thật. "
                      "Ít nhất một practical_example là tình huống vận dụng gần đời sống/lớp học, tối đa 2 câu; "
                      "nếu không có ví dụ thật trong nguồn, ghi rõ 'Tình huống giả định:' và chỉ áp dụng nguyên lý có nguồn. "
                      "Đổi nhịp giữa quan sát ảnh, giải thích, quy trình và vận dụng; tránh mọi slide cùng dạng bullet. "
                      "Trả về design gồm theme và một thiết kế cho mỗi slide_id. Chọn bố cục dựa trên nội dung: "
                      "statement cho một thông điệp nổi bật, two_columns khi có hai nhóm ý để đối chiếu, "
                      "example khi tình huống là trọng tâm, figure cho hình nguồn, photo cho ảnh minh họa, "
                      "process cho trình tự thực sự, points cho các ý độc lập. rationale giải thích lựa chọn cụ thể. "
                      "Theo nguyên tắc slides_maker: tiêu đề nêu ý chính, một slide một thông điệp, bullet là cụm từ "
                      "ngắn thay vì đoạn văn; giải thích dài để lời giảng. Ưu tiên hình có ý nghĩa, phân cấp rõ và "
                      "khoảng trống; không thêm số liệu hoặc chi tiết không có nguồn để trang trí.",
                      {"request": request.model_dump(), "source": context,
                       "figures": [{"id": u.id, "page": u.page, "description": u.content[:200]}
                                   for u in source.units if u.asset_key and f"[{u.id} |" in context]}, example,
                      context_stats=(full, selected), images=source_previews(source, context),
                      output_limit=2500 + 400 * request.slide_count)
    if len(result.slide_content.slides) != request.slide_count:
        raise ValueError("Model trả về số slide không khớp yêu cầu")
    require_sections(result.slide_content)
    slides = [s.model_copy(update={"teaching_script": None}) for s in result.slide_content.slides]
    used = {e for s in slides for e in s.evidence_ids}
    content = result.slide_content.model_copy(update={"slides": slides,
        "omitted_source_ids": [u.id for u in source.units if u.id not in used]})
    design = result.design or create_design(content)
    if (len(design.designs) != len(slides)
            or {d.slide_id for d in design.designs} != {s.id for s in slides}):
        raise ValueError("Thiết kế phải khớp đủ từng slide, không trùng hoặc thiếu slide_id")
    return Draft(lesson=result.lesson, slide_content=content, design=design)


def create_design(content):
    return DesignPlan(theme="ocean", designs=[SlideDesign(slide_id=s.id,
        layout="figure" if s.figure_id else (
            "process" if s.visual and s.visual.kind == "process" and len(s.bullets) >= 2 else
            "photo" if s.visual and s.visual.kind in {"photo", "illustration"} else
            "example" if s.practical_example else "two_columns" if len(s.bullets) >= 4 else "points"),
        rationale="Chọn bố cục theo hình, quy trình và tình huống vận dụng.") for s in content.slides])


def prepare_scripts(draft, previous=None):
    if previous is None:
        return draft
    old_slides = {s.id: s for s in previous.slide_content.slides}
    old_activities = {a.id: a.model_dump() for a in previous.lesson.activities}
    new_activities = {a.id: a.model_dump() for a in draft.lesson.activities}
    old_designs = {d.slide_id: d for d in previous.design.designs}
    new_designs = {d.slide_id: d for d in draft.design.designs}
    def neighborhood(items, slide_id):
        index = next((i for i, s in enumerate(items) if s.id == slide_id), None)
        if index is None:
            return None
        return [s.model_dump(exclude={"teaching_script"}) for s in items[max(0, index-1):index+2]]
    slides = []
    for slide in draft.slide_content.slides:
        old = old_slides.get(slide.id)
        if old:
            changed = (slide.model_dump(exclude={"teaching_script"}) != old.model_dump(exclude={"teaching_script"}) or
                       old_activities.get(slide.activity_id) != new_activities.get(slide.activity_id) or
                       old_designs.get(slide.id) != new_designs.get(slide.id) or
                       draft.design.theme != previous.design.theme or
                       draft.lesson.model_dump(exclude={"activities"}) != previous.lesson.model_dump(exclude={"activities"}) or
                       draft.slide_content.sections != previous.slide_content.sections or
                       neighborhood(draft.slide_content.slides, slide.id) != neighborhood(previous.slide_content.slides, slide.id))
            # Explicit teacher script edits survive; unchanged scripts are invalidated by content edits.
            if changed and slide.teaching_script == old.teaching_script:
                slide = slide.model_copy(update={"teaching_script": None})
        slides.append(slide)
    return draft.model_copy(update={"slide_content": draft.slide_content.model_copy(update={"slides": slides})})


def create_scripts(gen, request, draft, source, rendered):
    slides = list(draft.slide_content.slides)
    known = {u.id for u in source.units}
    pending = []
    for index, slide in enumerate(slides):
        if slide.teaching_script:
            continue
        if any(e not in known for e in slide.evidence_ids):
            script = TeachingScript(introduction="", narration="Chưa thể soạn lời giảng: cần sửa nguồn của slide.",
                                    transition="", estimated_seconds=5, evidence_ids=slide.evidence_ids, questions=[])
            slides[index] = slide.model_copy(update={"teaching_script": script})
        else:
            pending.append(index)
    batch_size = settings().script_batch_size
    for offset in range(0, len(pending), batch_size):
        indices = pending[offset:offset + batch_size]
        batch = [slides[i] for i in indices]
        ids = {e for slide in batch for e in slide.evidence_ids}
        ids.update(s.figure_id for s in batch if s.figure_id)
        activities = [a for a in draft.lesson.activities if a.id in {s.activity_id for s in batch}]
        ids.update(e for a in activities for e in a.evidence_ids)
        context, full, selected = select_context(source, " ".join(s.title for s in batch),
                                               settings().context_tokens, ids, request.context_mode)
        def example(batch=batch):
            items = []
            for slide in batch:
                unit = next(u for u in source.units if u.id == slide.evidence_ids[0])
                items.append(ScriptItem(slide_id=slide.id, script=TeachingScript(
                    introduction="Chúng ta cùng xem nội dung trên slide này.",
                    narration=f"Tại trang {unit.page}, tài liệu trình bày: {unit.content[:900]}. "
                              "Hãy giải thích ý chính bằng lời của mình.",
                    transition="Hãy kết nối ý chính với phần tiếp theo.",
                    estimated_seconds=max(20, request.duration_minutes * 40 // len(slides)),
                    evidence_ids=slide.evidence_ids, questions=[])))
            return ScriptBatch(items=items).model_dump()
        result = gen.call("scripts:" + ",".join(s.id for s in batch), ScriptBatch,
            "Viết lời giảng có thể nói thành lời cho các slide theo thứ tự ảnh. Ảnh đầu là bảng slide của nhóm; "
            "các ảnh sau là nguồn OCR. Giải thích ý/hình, không đọc lại bullet; kết nối tiêu đề trước/sau. "
            "Mỗi slide một item với đúng slide_id, lời giảng ngắn gọn; câu hỏi/đáp án riêng. "
            "Tổng estimated_seconds và wait_seconds trong nhóm không vượt seconds_budget. Chỉ dùng nguồn đã cho. "
            "Dựa vào sections (K) để giới thiệu đầu phần, tổng kết cuối phần và chuyển giữa các phần kiến thức.",
            {"slides": [s.model_dump(exclude={"teaching_script"}) for s in batch],
             "sections": [k.model_dump() for k in draft.slide_content.sections],
             "neighbors": [{"slide_id": slides[i].id, "previous": slides[i-1].title if i else None,
                            "next": slides[i+1].title if i+1 < len(slides) else None} for i in indices],
             "audience": request.audience, "requirements": request.requirements,
             "activities": [a.model_dump() for a in activities],
             "visuals": {s.id: {k: v for k, v in rendered.get("media", {}).get(s.id, {}).items()
                                 if k in {"origin", "caption", "title", "reason"}} for s in batch},
             "seconds_budget": request.duration_minutes * 60 * len(batch) // len(slides), "source": context},
            example, images=[contact_sheet(gen.job_id, rendered, indices), *source_previews(source, "", ids)],
            context_stats=(full, selected), output_limit=1000 + 1200 * len(batch))
        scripts = {item.slide_id: item.script for item in result.items}
        if set(scripts) != {s.id for s in batch} or len(result.items) != len(batch):
            raise ValueError("Nhóm lời giảng thiếu, trùng hoặc sai slide_id")
        for index in indices:
            slides[index] = slides[index].model_copy(update={"teaching_script": scripts[slides[index].id]})
    return draft.model_copy(update={"slide_content": draft.slide_content.model_copy(update={"slides": slides})})


def contact_sheet(job_id, rendered, indices=None):
    storage = Storage()
    thumbs = []
    indices = list(range(rendered["slide_count"])) if indices is None else indices
    for i in indices:
        key = rendered["files"][f"render/slide-{i+1}.png"]
        storage.get(key)
        with Image.open(storage.path(key)) as img:
            thumbs.append(ImageOps.pad(img.convert("RGB"), (480, 270), color="white"))
    sheet = Image.new("RGB", (960, 270 * ((len(thumbs) + 1)//2)), "#dddddd")
    for i, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((i % 2)*480, (i//2)*270))
    path = settings().data_dir / "work" / job_id / f"contact-{digest([rendered, indices])[:12]}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    return path


def review_draft(gen, request, draft, source, rendered):
    evidence_ids = draft_evidence(draft)
    context, full, selected = select_context(source, draft.lesson.title, settings().context_tokens,
                                             evidence_ids, request.context_mode)
    allowed_ids = [u.id for u in source.units if f"[{u.id} |" in context]
    result = gen.call("review", CombinedReview,
        "Kiểm tra chung bốn tiêu chí, không chỉnh bài: pedagogy (trình tự, độ rõ, tải nhận thức), "
        "content (đúng nguồn, lời giảng, đáp án; sai hoặc thiếu căn cứ là blocked), "
        "assessment (mục tiêu/hoạt động/câu hỏi, thời lượng, không lộ đáp án), "
        "slide_critic (ảnh render, tương phản, cắt chữ/hình, khớp lời giảng). "
        "Ảnh đầu là bảng slide; các ảnh sau là PDF OCR. Chỉ báo lỗi cụ thể, tối đa 3 finding mỗi tiêu chí, "
        "target là slide/activity/objective ID hoặc lesson; nêu evidence và cách sửa. Không khẳng định kiểm tra chưa làm. "
        "evidence_ids chỉ được lấy nguyên văn từ allowed_evidence_ids; không dùng slide ID, K ID, "
        "số trang hay mã tự tạo làm evidence. Với nhận xét bố cục không cần dẫn PDF, dùng evidence_ids=[]. "
        "Viết message và suggestion ngắn gọn, không lặp ý; trả về JSON đầy đủ theo schema. "
        "Kiểm tra ảnh có đúng chủ thể, gây hiểu nhầm, hình AI giống ảnh sự kiện thật không; tình huống giả định phải ghi rõ. "
        "Ảnh Internet/AI chỉ minh họa, không phải bằng chứng cho kiến thức. Thiếu ảnh không tự động là lỗi blocked.",
        {"request": request.model_dump(), "draft": prompt_draft(draft), "source": context,
         "allowed_evidence_ids": allowed_ids,
         "visuals": {sid: {k: v for k, v in item.items() if k in {"origin", "title", "caption", "reason"}}
                     for sid, item in rendered.get("media", {}).items()}},
        lambda: {peer: Review(peer=peer, status="pass", findings=[]).model_dump()
                 for peer in CombinedReview.model_fields},
        images=[contact_sheet(gen.job_id, rendered), *source_previews(source, context, evidence_ids)],
        context_stats=(full, selected), output_limit=6000)
    known = {u.id for u in source.units}
    unknown = sorted({e for peer in CombinedReview.model_fields
                      for f in getattr(result, peer).findings for e in f.evidence_ids if e not in known})
    if unknown:
        result = gen.call("review:repair_evidence", CombinedReview,
            "Sửa các dẫn nguồn sai của bản phản biện. Chỉ dùng allowed_evidence_ids có thật trong nguồn; "
            "không đoán ánh xạ từ số trang, slide ID hoặc K ID. Đối chiếu lại nội dung nhận xét với nguồn. "
            "Nhận xét bố cục không cần PDF được dùng evidence_ids=[]. Nếu không thể xác minh nhận xét kiến thức, "
            "giữ severity=blocked và giải thích rõ chưa xác minh được nguồn; không chuyển thành pass. "
            "Giữ đủ bốn tiêu chí và các vấn đề chưa được xử lý. Trả JSON đầy đủ, ngắn gọn.",
            {"review": result.model_dump(), "invalid_evidence_ids": unknown,
             "allowed_evidence_ids": allowed_ids, "source": context, "draft": prompt_draft(draft)},
            lambda: result.model_dump(), context_stats=(full, selected), output_limit=6000)
    reviews = [grounded_review(getattr(result, peer), peer, known) for peer in CombinedReview.model_fields]
    reviews.append(validate_draft(draft, source, request.duration_minutes))
    storage = Storage()
    geometry = storage.get_json(rendered["files"]["geometry.json"])
    lint_report = storage.get_json(rendered["files"]["lint.json"])
    findings = []
    for entry in geometry["geometry"]:
        if entry[1] == "CRITICAL":
            findings.append(Finding(id=f"render-{len(findings)+1}", severity="blocked", target=f"slide-{entry[0]}",
                                    message=str(entry[3]), suggestion="Giảm lượng chữ hoặc đổi bố cục.", evidence_ids=[]))
    if geometry["hard_count"]:
        findings.append(Finding(id="render-lint", severity="blocked", target="design",
                                message=f"slides_maker phát hiện {geometry['hard_count']} lỗi bố cục: " + str(lint_report.get("findings", []))[:2200],
                                suggestion="Sửa nội dung hoặc bố cục rồi render lại.", evidence_ids=[]))
    reviews.append(Review(peer="render", status="blocked" if findings else "pass", findings=findings))
    return reviews


def revise_draft(gen, request, draft, source, feedback):
    context, full, selected = select_context(source, draft.lesson.title + feedback, settings().context_tokens,
                                             draft_evidence(draft), request.context_mode)
    revised = gen.call("revision", Draft,
                       "Bạn là Lead duy nhất sửa bài. Xử lý feedback và findings, giữ ID ổn định. "
                       "Không xóa nội dung đúng không liên quan. Giữ số slide; nếu sửa slide để teaching_script=null cho script sinh lại. "
                       "Giữ nguồn hợp lệ, hoạt động khớp mục tiêu, thời lượng đúng yêu cầu. "
                       "Cập nhật sections (K) theo nội dung: mỗi slide thuộc đúng một phần kiến thức, "
                       "các phần chứa slide liên tiếp và phủ hết bộ slide theo thứ tự trình chiếu.",
                       {"request": request.model_dump(), "draft": prompt_draft(draft), "feedback": feedback, "source": context},
                         lambda: draft.model_dump(), context_stats=(full, selected), images=source_previews(source, context),
                         output_limit=2500 + 450 * request.slide_count)
    if len(revised.slide_content.slides) != request.slide_count:
        raise ValueError("Model trả về số slide không khớp yêu cầu")
    require_sections(revised.slide_content)
    used = {e for slide in revised.slide_content.slides for e in slide.evidence_ids}
    revised.slide_content.omitted_source_ids = [u.id for u in source.units if u.id not in used]
    return prepare_scripts(revised, draft)


def prompt_draft(draft):
    # Derived coverage lists can dwarf the lesson; reviewers do not need them.
    return draft.model_dump(exclude={"slide_content": {"omitted_source_ids"}})


def draft_evidence(draft):
    ids = {e for o in draft.lesson.objectives for e in o.evidence_ids}
    ids.update(e for a in draft.lesson.activities for e in a.evidence_ids)
    for slide in draft.slide_content.slides:
        ids.update(slide.evidence_ids)
        if slide.figure_id:
            ids.add(slide.figure_id)
        if slide.teaching_script:
            ids.update(slide.teaching_script.evidence_ids)
            ids.update(e for q in slide.teaching_script.questions for e in q.evidence_ids)
    return ids
