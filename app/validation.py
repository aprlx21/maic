from app.schemas import Draft, Finding, Review, SourceDocument


def validate_draft(draft: Draft, source: SourceDocument, duration_minutes: int, require_scripts=True):
    findings = []
    evidence = {u.id: u for u in source.units}
    objectives = {o.id for o in draft.lesson.objectives}
    activities = {a.id for a in draft.lesson.activities}

    def add(target, message, severity="blocked"):
        findings.append(Finding(id=f"validation-{len(findings)+1}", severity=severity, target=target,
                                message=message, suggestion="Sửa nội dung hoặc liên kết nguồn rồi phản biện lại.", evidence_ids=[]))

    def refs(target, ids):
        if not ids or any(i not in evidence for i in ids):
            add(target, "Thiếu nguồn hoặc evidence ID không tồn tại.")

    for collection, name in [(draft.lesson.objectives, "mục tiêu"), (draft.lesson.activities, "hoạt động"),
                              (draft.slide_content.slides, "slide")]:
        if len({item.id for item in collection}) != len(collection):
            add("lesson", f"ID {name} bị trùng.")
    for objective in draft.lesson.objectives:
        refs(objective.id, objective.evidence_ids)
    for activity in draft.lesson.activities:
        refs(activity.id, activity.evidence_ids)
        if any(i not in objectives for i in activity.objective_ids):
            add(activity.id, "Hoạt động tham chiếu mục tiêu không tồn tại.")
    total = sum(a.minutes for a in draft.lesson.activities)
    if total != duration_minutes:
        add("lesson", f"Tổng thời lượng hoạt động {total} phút khác yêu cầu {duration_minutes} phút.", "revise")
    slide_ids = {s.id for s in draft.slide_content.slides}
    sections = draft.slide_content.sections
    if sections:
        if len({k.id for k in sections}) != len(sections):
            add("sections", "ID phần kiến thức K bị trùng.")
        assigned = [sid for k in sections for sid in k.slide_ids]
        if assigned != [s.id for s in draft.slide_content.slides]:
            add("sections", "Các phần K phải phủ mỗi slide đúng một lần, theo thứ tự trình chiếu và liên tiếp.")
    if {d.slide_id for d in draft.design.designs} != slide_ids or len(draft.design.designs) != len(slide_ids):
        add("design", "Thiết kế chưa khớp đủ các slide.")
    designs = {d.slide_id: d for d in draft.design.designs}
    for slide in draft.slide_content.slides:
        refs(slide.id, slide.evidence_ids)
        if slide.activity_id not in activities:
            add(slide.id, "Slide tham chiếu hoạt động không tồn tại.")
        if slide.figure_id and (slide.figure_id not in evidence or not evidence[slide.figure_id].asset_key):
            add(slide.id, "Hình minh họa không có asset nguồn hợp lệ.")
        if slide.id in designs and designs[slide.id].layout == "figure" and not slide.figure_id:
            add(slide.id, "Bố cục hình cần một hình nguồn.")
        if slide.id in designs and designs[slide.id].layout == "process" and len(slide.bullets) < 2:
            add(slide.id, "Sơ đồ quy trình cần ít nhất hai bước.", "revise")
        if any(len(b) > 240 for b in slide.bullets):
            add(slide.id, "Một ý trên slide quá dài để trình chiếu.", "revise")
        script = slide.teaching_script
        if require_scripts and not script:
            add(slide.id, "Slide chưa có script giảng dạy.")
        if script:
            refs(slide.id + "/script", script.evidence_ids)
            for question in script.questions:
                refs(slide.id + "/question", question.evidence_ids)
    if require_scripts:
        seconds = sum(s.teaching_script.estimated_seconds + sum(q.wait_seconds for q in s.teaching_script.questions)
                      for s in draft.slide_content.slides if s.teaching_script)
        if seconds > duration_minutes * 60:
            add("scripts", f"Lời giảng và thời gian hỏi đáp ({seconds//60} phút) vượt thời lượng bài.", "revise")
    for page in source.pages:
        if page.status == "needs_review":
            add(f"page-{page.page_no}", f"Trang {page.page_no} chưa trích xuất thành công. Cần PDF có văn bản đọc được.")
    return Review(peer="validation", status="blocked" if any(f.severity == "blocked" for f in findings)
                  else "revise" if findings else "pass", findings=findings)


def grounded_review(review: Review, peer: str, known_ids: set[str]):
    """Keep faulty findings visible and block approval without inventing source links."""
    findings = []
    for finding in review.findings:
        unknown = list(dict.fromkeys(e for e in finding.evidence_ids if e not in known_ids))
        if unknown:
            finding = finding.model_copy(update={
                "severity": "blocked",
                "message": ("Phản biện chưa xác minh được nguồn: " + ", ".join(unknown)[:500]
                            + ". Nhận xét cần kiểm tra lại: " + finding.message)[:3000],
                "suggestion": ("Đối chiếu PDF và chạy lại phản biện với evidence ID hợp lệ. "
                               + finding.suggestion)[:3000],
                "evidence_ids": [e for e in finding.evidence_ids if e in known_ids],
            })
        findings.append(finding)
    return normalized_review(review.model_copy(update={"findings": findings}), peer)


def normalized_review(review: Review, peer: str):
    findings = [f.model_copy(update={"id": f"{peer}-{i+1}"}) for i, f in enumerate(review.findings)]
    if review.status in {"blocked", "revise"} and not findings:
        findings = [Finding(id=f"{peer}-1", severity=review.status, target="lesson",
                            message="Reviewer chưa cung cấp giải thích đủ rõ.", suggestion="Chạy lại phản biện.", evidence_ids=[])]
    status = "blocked" if any(f.severity == "blocked" for f in findings) else (
        "revise" if any(f.severity == "revise" for f in findings) else "pass")
    return Review(peer=peer, status=status, findings=findings)
