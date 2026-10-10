import hashlib
import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from sqlalchemy import func, select

from app.config import settings
from app.context import build_tree
from app.db import Event, Job, Publication, Revision, event, session, set_status
from app.document import read_document
from app.generation import (
    create_draft,
    create_scripts,
    prepare_scripts,
    review_draft,
    revise_draft,
)
from app.llm import Generator
from app.rendering import (
    attach_notes,
    convert_docx_pdf,
    export_docx,
    export_speaker_handout,
    render_draft,
    renderer_backend,
)
from app.schemas import Decision, Draft, KnowledgeTree, LessonRequest, SourceDocument, digest
from app.storage import Storage
from app.visuals import prepare_media


class State(TypedDict, total=False):
    job_id: str
    source: dict
    tree: dict
    lesson: dict
    draft: dict
    rendered: dict
    media: dict
    reviews: list
    revision_id: str
    rounds: int
    cycle_id: str
    decision: dict
    command_id: str


def job_data(job_id):
    with session() as db:
        job = db.get(Job, job_id)
        return job, LessonRequest.model_validate(job.request)


def check_approval(revision, decision):
    if revision.content_hash != decision.approval_hash or revision.id != decision.revision_id:
        raise ValueError("Bản duyệt đã thay đổi. Hãy tải lại revision hiện tại.")
    findings = [f for r in revision.reviews for f in r["findings"]]
    if any(f["severity"] == "blocked" for f in findings):
        raise ValueError("Không thể duyệt khi còn finding blocked")
    for finding in findings:
        if finding["severity"] == "revise" and not decision.accepted_findings.get(finding["id"], "").strip():
            raise ValueError("Cần ghi lý do chấp nhận cho từng finding revise chưa xử lý")
    required = {"pedagogy", "content", "assessment", "slide_critic", "validation", "render"}
    if {r["peer"] for r in revision.reviews} != required:
        raise ValueError("Revision chưa hoàn tất tất cả phản biện")


def read_node(state):
    started = time.monotonic()
    job, _ = job_data(state["job_id"])
    set_status(job.id, "reading", "Đọc PDF và chuẩn hóa nguồn theo trang")
    source, cached = read_document(job.source_key, job.source_hash)
    storage = Storage()
    storage.put_json(f"jobs/{job.id}/source.json", source.model_dump())
    tree_key = f"sources/{job.source_hash}/{source.parser_version}/knowledge-tree.json"
    if storage.exists(tree_key):
        tree = KnowledgeTree.model_validate(storage.get_json(tree_key))
    else:
        tree = build_tree(source)
        storage.put_json(tree_key, tree.model_dump())
    event(job.id, "reading", "Đã dùng cache PDF" if cached else "Đã trích nội dung và lưu cache",
          {"pages": len(source.pages), "units": len(source.units), "cached": cached, "seconds": time.monotonic() - started})
    unreadable = [str(p.page_no) for p in source.pages if p.status == "needs_review"]
    if unreadable:
        raise ValueError("Chưa đọc được trang " + ", ".join(unreadable)
                         + ". Cấu hình OCR hoặc gửi PDF rõ hơn trước khi gọi AI.")
    return {"source": source.model_dump(), "tree": tree.model_dump(), "rounds": 0, "cycle_id": "initial"}


def draft_node(state):
    job, request = job_data(state["job_id"])
    # Avoid provider charges and source transfer if this host cannot complete the required exports.
    renderer_backend()
    set_status(job.id, "planning", "Lead soạn giáo án và nội dung slide trong một lượt")
    draft = create_draft(Generator(job.id), request, SourceDocument.model_validate(state["source"]))
    return {"draft": draft.model_dump()}


def media_node(state):
    job, request = job_data(state["job_id"])
    set_status(job.id, "illustrating", "Chuẩn bị ảnh Internet và minh họa AI theo ngân sách")
    return {"media": prepare_media(job.id, request, Draft.model_validate(state["draft"]), job.mode)}


def render_node(state):
    started = time.monotonic()
    job, _ = job_data(state["job_id"])
    set_status(job.id, "rendering", "DeckKit dựng PPTX và kiểm tra bản render")
    draft = Draft.model_validate(state["draft"])
    rendered = render_draft(job.id, draft, SourceDocument.model_validate(state["source"]), job.mode,
                            media=state.get("media", {}))
    event(job.id, "rendering", "Đã dựng và kiểm tra slide", {"seconds": time.monotonic() - started})
    return {"rendered": rendered}


def scripts_node(state):
    job, request = job_data(state["job_id"])
    set_status(job.id, "scripting", "Soạn lời giảng theo nhóm slide đã render")
    draft = create_scripts(Generator(job.id), request, Draft.model_validate(state["draft"]),
                           SourceDocument.model_validate(state["source"]), state["rendered"])
    rendered = attach_notes(job.id, draft, state["rendered"])
    return {"draft": draft.model_dump(), "rendered": rendered}


def review_node(state):
    job, request = job_data(state["job_id"])
    set_status(job.id, "reviewing", "Kiểm tra chung sư phạm, nội dung, đánh giá và bản dựng")
    draft = Draft.model_validate(state["draft"])
    reviews = review_draft(Generator(job.id), request, draft, SourceDocument.model_validate(state["source"]), state["rendered"])
    operation = f"{state['cycle_id']}:{state['rounds']}"
    storage = Storage()
    hashes = {name: hashlib.sha256(storage.get(key)).hexdigest()
              for name, key in state["rendered"]["files"].items()}
    content_hash = digest({"draft": state["draft"], "source_hash": job.source_hash, "artifacts": hashes})
    with session() as db:
        revision = db.scalar(select(Revision).where(Revision.job_id == job.id, Revision.operation_key == operation))
        if not revision:
            number = (db.scalar(select(func.max(Revision.number)).where(Revision.job_id == job.id)) or 0) + 1
            revision = Revision(job_id=job.id, number=number, operation_key=operation, draft=state["draft"],
                                content_hash=content_hash, artifacts={**state["rendered"], "hashes": hashes},
                                reviews=[r.model_dump() for r in reviews])
            db.add(revision)
            db.flush()
        db.get(Job, job.id).current_revision = revision.id
        revision_id = revision.id
    return {"revision_id": revision_id, "reviews": [r.model_dump() for r in reviews]}


def review_route(state):
    problems = any(f["severity"] in {"blocked", "revise"} for r in state["reviews"] for f in r["findings"])
    return "auto_revision" if problems and state["rounds"] < settings().max_auto_rounds else "teacher"


def auto_revision_node(state):
    job, request = job_data(state["job_id"])
    set_status(job.id, "revising", f"Lead sửa theo phản biện, vòng {state['rounds']+1}/{settings().max_auto_rounds}")
    draft = revise_draft(Generator(job.id), request, Draft.model_validate(state["draft"]),
                          SourceDocument.model_validate(state["source"]), json.dumps(state["reviews"], ensure_ascii=False))
    return {"draft": draft.model_dump(), "rounds": state["rounds"] + 1}


def teacher_node(state):
    set_status(state["job_id"], "awaiting_teacher", "Chờ giáo viên xem, sửa hoặc duyệt bản hiện tại")
    value = interrupt({"revision_id": state["revision_id"], "actions": ["approve", "edit", "request_revision", "reject"]})
    return {"decision": value["decision"], "command_id": value["id"]}


def teacher_route(state):
    action = state["decision"]["action"]
    return "publish" if action == "approve" else "reject" if action == "reject" else "teacher_revision"


def teacher_revision_node(state):
    job, request = job_data(state["job_id"])
    decision = Decision.model_validate(state["decision"])
    set_status(job.id, "revising", "Tạo revision mới từ chỉnh sửa của giáo viên")
    previous = Draft.model_validate(state["draft"])
    if decision.action == "edit":
        draft = prepare_scripts(decision.draft, previous)
    else:
        draft = revise_draft(Generator(job.id), request, previous, SourceDocument.model_validate(state["source"]), decision.feedback)
    return {"draft": draft.model_dump(), "rounds": 0, "cycle_id": state["command_id"]}


def publish_node(state):
    job, _ = job_data(state["job_id"])
    decision = Decision.model_validate(state["decision"])
    with session() as db:
        existing = db.scalar(select(Publication).where(Publication.job_id == job.id, Publication.revision_id == state["revision_id"]))
        if existing:
            db.get(Job, job.id).status = "published"
            return {}
        revision = db.get(Revision, state["revision_id"])
        if job.current_revision != revision.id:
            raise ValueError("Revision hiện tại không khớp revision được duyệt")
        check_approval(revision, decision)
        version = (db.scalar(select(func.max(Publication.version)).where(Publication.job_id == job.id)) or 0) + 1
    set_status(job.id, "exporting", "Xuất giáo án, slide và package đã duyệt")
    draft = Draft.model_validate(revision.draft)
    storage = Storage()
    if hashlib.sha256(storage.get(job.source_key)).hexdigest() != job.source_hash:
        raise ValueError("PDF nguồn đã thay đổi; không thể phát hành revision này.")
    actual_hashes = {name: hashlib.sha256(storage.get(key)).hexdigest()
                     for name, key in revision.artifacts["files"].items()}
    expected_hash = digest({"draft": revision.draft, "source_hash": job.source_hash, "artifacts": actual_hashes})
    if expected_hash != decision.approval_hash:
        raise ValueError("File của revision đã thay đổi sau phản biện; cần dựng và duyệt lại.")
    source = SourceDocument.model_validate(state["source"])
    work = settings().data_dir / "work" / job.id / f"publish-{revision.id}"
    work.mkdir(parents=True, exist_ok=True)
    docx = work / "lesson-plan.docx"
    export_docx(draft, source, docx, job.mode)
    pdf = convert_docx_pdf(docx)
    handout = work / "speaker-notes.docx"
    export_speaker_handout(draft, revision.artifacts, handout)
    notes_pdf = convert_docx_pdf(handout)
    prefix = f"published/{job.id}/{version}"
    files = {}
    for name, data in {"lesson-plan.docx": docx.read_bytes(), "lesson-plan.pdf": pdf.read_bytes(),
                       "speaker-notes.pdf": notes_pdf.read_bytes(),
                       "slides.pptx": storage.get(revision.artifacts["files"]["slides.pptx"]),
                       "slides.pdf": storage.get(revision.artifacts["files"]["slides.pdf"]),
                       **{name: storage.get(key) for name, key in revision.artifacts["files"].items()
                          if name == "image-credits.json" or name.startswith("images/")}}.items():
        files[name] = storage.put(f"{prefix}/{name}", data)
    actions = []
    for slide in draft.slide_content.slides:
        actions.extend([{"type": "ShowFile", "slide_id": slide.id},
                        {"type": "ReadScript", "slide_id": slide.id, "script": slide.teaching_script.model_dump(exclude={"questions"})}])
        actions.extend({"type": "AskQuestion", "slide_id": slide.id, "prompt": q.prompt,
                        "wait_seconds": q.wait_seconds, "answer_key_id": f"{slide.id}-q{i+1}"}
                       for i, q in enumerate(slide.teaching_script.questions))
    answer_keys = {f"{s.id}-q{i+1}": {"answer": q.expected_answer, "evidence_ids": q.evidence_ids}
                   for s in draft.slide_content.slides for i, q in enumerate(s.teaching_script.questions)}
    package = {"schema_version": "1.0", "lesson_id": job.id, "version": version, "revision_id": revision.id,
               "generation_mode": job.mode, "approval_hash": revision.content_hash, "source_document_id": job.source_hash,
               "lesson": draft.lesson.model_dump(), "slides": [s.model_dump(exclude={"teaching_script"}) for s in draft.slide_content.slides],
               "teaching_actions": actions, "answer_keys": answer_keys, "knowledge_tree": state["tree"],
               "evidence": [u.model_dump() for u in source.units], "source_uri": job.source_key,
               "approval": decision.model_dump(exclude={"draft"}), "reviews": revision.reviews, "files": files,
               "file_sha256": {name: hashlib.sha256(storage.get(key)).hexdigest() for name, key in files.items()},
               "slides_maker_commit": json.loads((Path(__file__).resolve().parents[1] / "vendor/slides_maker.lock.json").read_text())["commit"]}
    package_key = storage.put_json(f"{prefix}/package.json", package)
    with session() as db:
        locked = db.get(Job, job.id, with_for_update=True)
        if locked.current_revision != revision.id:
            raise ValueError("Revision đã thay đổi trong lúc xuất")
        db.add(Publication(job_id=job.id, revision_id=revision.id, version=version, approval_hash=revision.content_hash,
                           teacher_name=decision.teacher_name, approval=decision.model_dump(exclude={"draft"}),
                           artifacts=files, package_key=package_key))
        locked.status = "published"
        db.add(Event(job_id=job.id, stage="published", message=f"Đã phát hành phiên bản {version}",
                     details={"teacher_name": decision.teacher_name, "approval_hash": revision.content_hash}))
    return {}


def reject_node(state):
    set_status(state["job_id"], "rejected", "Giáo viên đã từ chối bản bài dạy")
    return {}


def make_graph(checkpointer):
    graph = StateGraph(State)
    for name, fn in [("read", read_node), ("draft", draft_node), ("media", media_node), ("render", render_node),
                     ("scripts", scripts_node), ("review", review_node), ("auto_revision", auto_revision_node),
                     ("teacher", teacher_node), ("teacher_revision", teacher_revision_node), ("publish", publish_node), ("reject", reject_node)]:
        graph.add_node(name, fn)
    for start, end in [(START, "read"), ("read", "draft"), ("draft", "media"), ("media", "render"),
                       ("render", "scripts"), ("scripts", "review"), ("auto_revision", "media"),
                       ("teacher_revision", "media"), ("publish", END), ("reject", END)]:
        graph.add_edge(start, end)
    # These aliases let checkpoints paused at the old authoring nodes finish on the new path.
    for legacy in ("lesson", "slides"):
        graph.add_node(legacy, draft_node)
        graph.add_edge(legacy, "media")
    graph.add_conditional_edges("review", review_route, ["auto_revision", "teacher"])
    graph.add_conditional_edges("teacher", teacher_route, ["publish", "reject", "teacher_revision"])
    return graph.compile(checkpointer=checkpointer)


@contextmanager
def persistent_graph():
    url = settings().checkpoint_url
    if url.startswith("sqlite:///"):
        from langgraph.checkpoint.sqlite import SqliteSaver
        with SqliteSaver.from_conn_string(url.removeprefix("sqlite:///")) as saver:
            yield make_graph(saver)
    else:
        from filelock import FileLock
        from langgraph.checkpoint.postgres import PostgresSaver
        with PostgresSaver.from_conn_string(url.replace("postgresql+psycopg://", "postgresql://")) as saver:
            with FileLock(str(settings().data_dir / "checkpoint-init.lock")):
                saver.setup()
            yield make_graph(saver)


def execute(job_id):
    with persistent_graph() as graph:
        config = {"configurable": {"thread_id": job_id}, "recursion_limit": 100}
        snapshot = graph.get_state(config)
        job, _ = job_data(job_id)
        command = job.pending_command
        has_interrupt = any(task.interrupts for task in snapshot.tasks)
        if command and snapshot.values and not snapshot.next and snapshot.values.get("command_id") != command["id"]:
            # Editing a published lesson starts a new revision, keeping prior packages immutable.
            graph.update_state(config, {"decision": command["decision"], "command_id": command["id"]}, as_node="teacher")
            value = None
        elif command and has_interrupt and snapshot.values.get("command_id") != command["id"]:
            value = Command(resume=command)
        elif snapshot.values:
            value = None
        else:
            value = {"job_id": job_id}
        return graph.invoke(value, config)
