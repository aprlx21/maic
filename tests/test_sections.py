import copy

import pytest

from app.generation import require_sections
from app.schemas import SlideContentPlan
from app.worker import run_once
from tests.conftest import upload
from tests.test_workflow import current, decision


def test_sections_cover_slides_and_survive_publication(client, pdf_bytes, fake_render):
    job_id = upload(client, pdf_bytes)
    run_once()
    revision = current(client, job_id)["revision"]
    content = revision["draft"]["slide_content"]
    assert content["sections"]
    assert [sid for k in content["sections"] for sid in k["slide_ids"]] == [s["id"] for s in content["slides"]]
    require_sections(SlideContentPlan.model_validate(content))
    for case in ("missing", "duplicate", "order"):
        broken = copy.deepcopy(content)
        if case == "missing":
            broken["sections"] = []
        elif case == "duplicate":
            broken["sections"][0]["slide_ids"].append(content["slides"][0]["id"])
        else:
            broken["sections"].reverse()
        with pytest.raises(ValueError, match="K"):
            require_sections(SlideContentPlan.model_validate(broken))
    assert decision(client, job_id, revision).status_code == 202
    run_once()
    detail = current(client, job_id)
    assert detail["status"] == "published"
    assert detail["revision"]["draft"]["slide_content"]["sections"] == content["sections"]
