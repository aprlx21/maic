import pytest

from app.budget import BudgetExceeded, execution_budget, remaining_seconds
from app.context import select_context, tokens, unit_text
from app.schemas import ContentUnit, PageRecord, SourceDocument


def test_retrieval_preserves_required_page_evidence_and_reduces_context():
    units = [ContentUnit(id=f"p{i:03}-u001", page=i, kind="paragraph", content=(f"Topic {i}. " + "water cycle " * 120),
                         bbox=[0, 0, 100, 100]) for i in range(1, 21)]
    source = SourceDocument(document_id="fixture", parser_version="test", source_key="fixture.pdf", units=units,
                            warnings=[], pages=[PageRecord(page_no=u.page, status="text", unit_ids=[u.id],
                                                           markdown_key=f"{u.page}.md", preview_key=f"{u.page}.png") for u in units])
    context, full, selected = select_context(source, "Topic 20", 1000, [units[-1].id])
    assert "p020-u001 | trang 20" in context
    assert selected < full / 2
    _, baseline, baseline_selected = select_context(source, "Topic 20", 1000, mode="full")
    assert baseline == baseline_selected == full


def test_time_budget_and_expiration():
    with execution_budget("test", -1), pytest.raises(BudgetExceeded):
        remaining_seconds("test")
    assert remaining_seconds("test") > 0


def test_required_evidence_cannot_exceed_context_limit():
    unit = ContentUnit(id="p001-u001", page=1, kind="paragraph", content="water cycle " * 100,
                       bbox=[0, 0, 100, 100])
    source = SourceDocument(document_id="test", parser_version="test", source_key="test.pdf",
                            units=[unit], pages=[], warnings=[])
    with pytest.raises(ValueError, match="MAIC_CONTEXT_TOKENS"):
        select_context(source, "water", tokens(unit_text(unit)) - 1, [unit.id])
    context, _, selected = select_context(source, "water", tokens(unit_text(unit)), [unit.id])
    assert context == unit_text(unit)
    assert selected == tokens(unit_text(unit))
