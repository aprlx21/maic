from app.llm import Generator
from app.schemas import Finding, Review
from app.validation import grounded_review
from app.worker import run_once
from tests.conftest import upload
from tests.test_workflow import current


def test_unknown_evidence_is_visible_and_blocks_approval():
    finding = Finding(id="f1", severity="info", target="s001", message="Check the claim",
                      suggestion="Read the source", evidence_ids=["real", "s001"])
    review = grounded_review(Review(peer="content", status="pass", findings=[finding]), "content", {"real"})
    assert review.status == "blocked"
    assert review.findings[0].evidence_ids == ["real"]
    assert "s001" in review.findings[0].message
    assert "Check the claim" in review.findings[0].message
    assert finding.evidence_ids == ["real", "s001"]


def test_invalid_reviewer_is_repaired_once_then_shown(client, pdf_bytes, fake_render, monkeypatch):
    original = Generator.call
    stages = []

    def invalid_review(self, stage, *args, **kwargs):
        stages.append(stage)
        result = original(self, stage, *args, **kwargs)
        if stage in {"review", "review:repair_evidence"}:
            result.content = Review(peer="content", status="revise", findings=[Finding(
                id="f1", severity="revise", target="s001", message="Check source",
                suggestion="Check again", evidence_ids=["nonexistent-evidence"])])
        return result

    monkeypatch.setattr(Generator, "call", invalid_review)
    job_id = upload(client, pdf_bytes)
    run_once()
    detail = current(client, job_id)
    assert detail["status"] == "awaiting_teacher", detail["error"]
    assert stages.count("review:repair_evidence") == 1
    review = next(r for r in detail["revision"]["reviews"] if r["peer"] == "content")
    assert review["status"] == "blocked"
    assert "nonexistent-evidence" in review["findings"][0]["message"]
