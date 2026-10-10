import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LessonRequest(Model):
    subject: str = Field(min_length=1, max_length=120)
    audience: str = Field(min_length=1, max_length=120)
    duration_minutes: int = Field(ge=10, le=240)
    requirements: str = Field(default="", max_length=4000)
    language: str = Field(default="Tiếng Việt", max_length=50)
    slide_count: int = Field(default=8, ge=3, le=60)
    context_mode: Literal["retrieved", "full"] = "retrieved"
    image_mode: Literal["source", "mixed", "internet", "ai"] = "source"


class ContentUnit(Model):
    id: str
    page: int = Field(ge=1)
    kind: Literal["heading", "paragraph", "table", "figure", "ocr"]
    content: str
    bbox: list[float] = Field(min_length=4, max_length=4)
    asset_key: str | None = None


class PageRecord(Model):
    page_no: int
    status: Literal["text", "ocr", "blank", "needs_review"]
    unit_ids: list[str]
    markdown_key: str
    preview_key: str
    warnings: list[str] = Field(default_factory=list)


class KnowledgeNode(Model):
    id: str
    parent_id: str | None
    title: str
    summary: str
    source_unit_ids: list[str]
    confidence: float = Field(ge=0, le=1)


class KnowledgeTree(Model):
    nodes: list[KnowledgeNode] = Field(min_length=1)


class SourceDocument(Model):
    document_id: str
    parser_version: str
    source_key: str
    pages: list[PageRecord]
    units: list[ContentUnit]
    warnings: list[str]


class Objective(Model):
    id: str
    text: str = Field(min_length=1, max_length=500)
    evidence_ids: list[str] = Field(min_length=1)


class Activity(Model):
    id: str
    title: str = Field(min_length=1, max_length=150)
    minutes: int = Field(ge=1, le=240)
    teacher_action: str = Field(max_length=2000)
    learner_action: str = Field(max_length=2000)
    assessment: str = Field(max_length=1500)
    objective_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)


class LessonPlan(Model):
    title: str = Field(min_length=1, max_length=200)
    audience: str
    objectives: list[Objective] = Field(min_length=1, max_length=12)
    prerequisites: list[str] = Field(max_length=15)
    materials: list[str] = Field(max_length=15)
    activities: list[Activity] = Field(min_length=1, max_length=20)
    homework: str = Field(max_length=3000)


class Question(Model):
    prompt: str = Field(min_length=1, max_length=1000)
    expected_answer: str = Field(min_length=1, max_length=2000)
    wait_seconds: int = Field(ge=5, le=600)
    evidence_ids: list[str] = Field(min_length=1)


class TeachingScript(Model):
    introduction: str = Field(max_length=1500)
    narration: str = Field(min_length=1, max_length=12000)
    transition: str = Field(max_length=1500)
    estimated_seconds: int = Field(ge=5, le=3600)
    evidence_ids: list[str] = Field(min_length=1)
    questions: list[Question] = Field(max_length=3)


class VisualPlan(Model):
    kind: Literal["photo", "illustration", "process"]
    query: str = Field(default="", max_length=120)
    brief: str = Field(default="", max_length=500)
    caption: str = Field(default="", max_length=160)


class Slide(Model):
    id: str
    title: str = Field(min_length=1, max_length=100)
    takeaway: str = Field(min_length=1, max_length=220)
    bullets: list[str] = Field(min_length=1, max_length=5)
    activity_id: str
    evidence_ids: list[str] = Field(min_length=1)
    figure_id: str | None = None
    visual: VisualPlan | None = None
    practical_example: str = Field(default="", max_length=280)
    teaching_script: TeachingScript | None = None


class KnowledgeSection(Model):
    id: str
    title: str = Field(min_length=1, max_length=150)
    summary: str = Field(min_length=1, max_length=500)
    slide_ids: list[str] = Field(min_length=1, max_length=60)


class SlideContentPlan(Model):
    narrative: str
    sections: list[KnowledgeSection] = Field(default_factory=list, max_length=60)
    slides: list[Slide] = Field(min_length=1, max_length=60)
    omitted_source_ids: list[str]


class SlideDesign(Model):
    slide_id: str
    layout: Literal["statement", "points", "two_columns", "figure", "photo", "process", "example"]
    rationale: str = Field(max_length=1000)


class DesignPlan(Model):
    theme: Literal["ocean", "forest", "ink"]
    designs: list[SlideDesign]


class Draft(Model):
    lesson: LessonPlan
    slide_content: SlideContentPlan
    design: DesignPlan


class LessonContent(Model):
    lesson: LessonPlan
    slide_content: SlideContentPlan
    design: DesignPlan | None = None


class ScriptItem(Model):
    slide_id: str
    script: TeachingScript


class ScriptBatch(Model):
    items: list[ScriptItem] = Field(min_length=1, max_length=8)


class Finding(Model):
    id: str
    severity: Literal["blocked", "revise", "info"]
    target: str
    message: str = Field(min_length=1, max_length=3000)
    suggestion: str = Field(max_length=3000)
    evidence_ids: list[str]


class Review(Model):
    peer: str
    status: Literal["pass", "revise", "blocked"]
    findings: list[Finding]


class CombinedReview(Model):
    pedagogy: Review
    content: Review
    assessment: Review
    slide_critic: Review


class Decision(Model):
    action: Literal["approve", "request_revision", "edit", "reject"]
    revision_id: str
    approval_hash: str
    teacher_name: str = Field(min_length=1, max_length=120)
    feedback: str = Field(default="", max_length=6000)
    accepted_findings: dict[str, str] = Field(default_factory=dict)
    draft: Draft | None = None


def digest(value) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
