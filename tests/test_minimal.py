import copy
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.budget import BudgetExceeded
from app.config import settings
from app.db import Job, Usage, session
from app.llm import Generator
from app.schemas import Review
from app.worker import run_once
from tests.conftest import upload
from tests.test_workflow import current, decision


@pytest.mark.parametrize("slide_count", [3, 8, 9])
def test_initial_call_count_and_approval_without_generation(client, pdf_bytes, fake_render, slide_count):
    job_id = upload(client, pdf_bytes)
    with session() as db:
        job = db.get(Job, job_id)
        job.request = {**job.request, "slide_count": slide_count}
    run_once()
    detail = current(client, job_id)
    assert detail["status"] == "awaiting_teacher"
    expected = ["draft", *["scripts:" + ",".join(f"s{i+1:03}" for i in range(start, min(start+8, slide_count)))
                          for start in range(0, slide_count, 8)], "review"]
    assert [u["stage"] for u in detail["usage"]] == expected
    run_once()
    assert len(current(client, job_id)["usage"]) == len(expected)
    assert decision(client, job_id, detail["revision"]).status_code == 202
    run_once()
    assert current(client, job_id)["status"] == "published"
    assert len(current(client, job_id)["usage"]) == len(expected)


def test_only_invalidated_scripts_are_regenerated(client, pdf_bytes, fake_render):
    job_id = upload(client, pdf_bytes)
    run_once()
    revision = current(client, job_id)["revision"]
    draft = copy.deepcopy(revision["draft"])
    draft["slide_content"]["slides"][0]["title"] = "Updated first slide"
    assert decision(client, job_id, revision, "edit", draft=draft).status_code == 202
    run_once()
    detail = current(client, job_id)
    assert [u["stage"] for u in detail["usage"]][3:] == ["scripts:s001,s002", "review"]
    assert detail["revision"]["draft"]["slide_content"]["slides"][2]["teaching_script"] == (
        revision["draft"]["slide_content"]["slides"][2]["teaching_script"])


def test_script_batch_failure_reuses_completed_batch(client, pdf_bytes, fake_render, monkeypatch):
    settings().script_batch_size = 2
    job_id = upload(client, pdf_bytes)
    original = Generator.call
    def fail_second_batch(self, stage, *args, **kwargs):
        if stage == "scripts:s003":
            raise RuntimeError("Temporary batch failure")
        return original(self, stage, *args, **kwargs)
    monkeypatch.setattr(Generator, "call", fail_second_batch)
    run_once()
    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "failed"
    monkeypatch.setattr(Generator, "call", original)
    assert client.post(f"/api/jobs/{job_id}/retry").status_code == 202
    run_once()
    stages = [u["stage"] for u in current(client, job_id)["usage"]]
    assert stages == ["draft", "scripts:s001,s002", "scripts:s003", "review"]


@pytest.mark.parametrize("legacy_node", ["lesson", "slides"])
def test_pending_legacy_checkpoint_can_resume(client, pdf_bytes, fake_render, legacy_node):
    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.graph import END, START, StateGraph

    from app.workflow import State, read_node

    job_id = upload(client, pdf_bytes)
    def old_step(state):
        raise RuntimeError("Old worker stopped")
    old = StateGraph(State)
    old.add_node("read", read_node)
    old.add_node(legacy_node, old_step)
    old.add_edge(START, "read")
    old.add_edge("read", legacy_node)
    old.add_edge(legacy_node, END)
    with (SqliteSaver.from_conn_string(settings().checkpoint_url.removeprefix("sqlite:///")) as saver,
          pytest.raises(RuntimeError, match="Old worker")):
        old.compile(checkpointer=saver).invoke({"job_id": job_id}, {"configurable": {"thread_id": job_id}})
    run_once()
    detail = current(client, job_id)
    assert detail["status"] == "awaiting_teacher"
    assert len([e for e in detail["events"] if e["details"].get("pages")]) == 1


@pytest.fixture
def provider(client, pdf_bytes, monkeypatch):
    job_id = upload(client, pdf_bytes)
    with session() as db:
        db.get(Job, job_id).mode = "openai"
    calls = []
    result = Review(peer="test", status="pass", findings=[])
    response = SimpleNamespace(output_parsed=result, usage=SimpleNamespace(
        input_tokens=123, output_tokens=45, input_tokens_details=SimpleNamespace(cached_tokens=20)))
    def parse(**kwargs):
        calls.append(kwargs)
        return response
    monkeypatch.setattr("app.llm.openai_api_key", lambda: "test-key")
    monkeypatch.setattr("app.llm.OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=parse)))
    return Generator(job_id), calls, response


def call(gen, **kwargs):
    return gen.call("test", Review, "Review.", {"source": "hello"}, dict, **kwargs)


def test_output_cap_actual_usage_and_cache(provider):
    gen, calls, _ = provider
    settings().max_call_output_tokens = 200
    first = call(gen, output_limit=500)
    assert calls[0]["max_output_tokens"] == 200
    assert call(gen, output_limit=500) == first
    assert len(calls) == 1
    with session() as db:
        row = db.scalar(select(Usage).where(Usage.job_id == gen.job_id))
        assert (row.input_tokens, row.output_tokens, row.cached_tokens) == (123, 45, 20)
    settings().max_call_output_tokens = 300
    call(gen, output_limit=500)
    assert len(calls) == 2  # Limit changes invalidate the response cache.


@pytest.mark.parametrize("limit,value", [
    ("max_call_input_tokens", 1), ("max_input_tokens", 1), ("max_output_tokens", 1),
])
def test_budget_stops_before_provider_call(provider, limit, value):
    gen, calls, _ = provider
    setattr(settings(), limit, value)
    with pytest.raises(BudgetExceeded):
        call(gen, output_limit=200)
    assert calls == []
    with session() as db:
        assert not list(db.scalars(select(Usage).where(Usage.job_id == gen.job_id)))


def test_failed_response_usage_is_kept_and_retry_does_not_reset_budget(provider):
    gen, calls, response = provider
    settings().max_model_calls = 1
    response.output_parsed = None
    with pytest.raises(ValueError):
        call(gen, output_limit=200)
    with session() as db:
        row = db.scalar(select(Usage).where(Usage.job_id == gen.job_id))
        assert row.status == "failed"
        assert (row.input_tokens, row.output_tokens) == (123, 45)
    with pytest.raises(BudgetExceeded):
        call(gen, output_limit=200)
    assert len(calls) == 1


def test_transport_failure_keeps_reserved_tokens(provider, monkeypatch):
    gen, calls, _ = provider
    def fail(**kwargs):
        calls.append(kwargs)
        raise TimeoutError("unknown provider usage")
    monkeypatch.setattr("app.llm.OpenAI", lambda **kwargs: SimpleNamespace(responses=SimpleNamespace(parse=fail)))
    with pytest.raises(TimeoutError):
        call(gen, output_limit=200)
    with session() as db:
        row = db.scalar(select(Usage).where(Usage.job_id == gen.job_id))
        assert row.status == "failed"
        assert row.input_tokens > 0
        assert row.output_tokens == 200


def test_default_does_not_automatically_revise(client, pdf_bytes, fake_render):
    job_id = upload(client, pdf_bytes)
    run_once()
    revision = current(client, job_id)["revision"]
    draft = copy.deepcopy(revision["draft"])
    draft["lesson"]["activities"][0]["minutes"] += 1
    assert decision(client, job_id, revision, "edit", draft=draft).status_code == 202
    run_once()
    detail = current(client, job_id)
    assert detail["status"] == "awaiting_teacher"
    assert len(detail["revisions"]) == 2
    assert "revision" not in [u["stage"] for u in detail["usage"]]
    assert decision(client, job_id, detail["revision"]).status_code == 409
