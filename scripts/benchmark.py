"""Run paired full/retrieved jobs against a running server; never auto-approve them."""
import argparse
import json
import time
from pathlib import Path

import httpx


def summarize(detail):
    usage = detail["usage"]
    completed = [u for u in usage if u["status"] == "complete"]
    source = detail.get("source") or {"units": [], "pages": []}
    known = {u["id"] for u in source["units"]}
    revision = detail.get("revision")
    refs = []
    if revision:
        draft = revision["draft"]
        for item in draft["lesson"]["objectives"] + draft["lesson"]["activities"] + draft["slide_content"]["slides"]:
            refs.extend(item["evidence_ids"])
        for slide in draft["slide_content"]["slides"]:
            script = slide.get("teaching_script")
            if script:
                refs.extend(script["evidence_ids"])
                refs.extend(e for q in script["questions"] for e in q["evidence_ids"])
    return {
        "job_id": detail["id"], "mode": detail["mode"], "context_mode": detail["request"]["context_mode"],
        "status": detail["status"], "error": detail["error"], "seconds": detail["elapsed_seconds"],
        "input_tokens": sum(u["input_tokens"] for u in completed),
        "output_tokens": sum(u["output_tokens"] for u in completed),
        "estimated_cost_usd": sum(u["cost_usd"] for u in usage) if usage and all(u["cost_usd"] is not None for u in usage) else None,
        "unconfirmed_calls": len(usage)-len(completed),
        "citation_id_validity": sum(e in known for e in refs) / len(refs) if refs else None,
        "source_unit_coverage": len(set(refs) & known) / len(known) if known else None,
        "unreadable_pages": [p["page_no"] for p in source["pages"] if p["status"] == "needs_review"],
        "stages": usage,
        "human_review_required": "Assess factual citation support, required concept coverage and OCR accuracy; valid IDs alone do not prove correctness."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdfs", nargs="+", type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--audience", default="Lớp 6")
    parser.add_argument("--minutes", type=int, default=45)
    parser.add_argument("--slides", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--output", type=Path, default=Path("data/benchmark.json"))
    args = parser.parse_args()
    report = []
    with httpx.Client(base_url=args.url, timeout=60) as client:
        for path in args.pdfs:
            for mode in ("full", "retrieved"):
                request = {"subject": args.subject, "audience": args.audience, "duration_minutes": args.minutes,
                           "slide_count": args.slides, "context_mode": mode}
                response = client.post("/api/jobs", files={"file": (path.name, path.read_bytes(), "application/pdf")},
                                       data={"request": json.dumps(request, ensure_ascii=False)})
                response.raise_for_status()
                job_id = response.json()["id"]
                deadline = time.monotonic() + args.timeout
                while True:
                    response = client.get(f"/api/jobs/{job_id}")
                    response.raise_for_status()
                    detail = response.json()
                    if not detail["processing"] or time.monotonic() >= deadline:
                        break
                    time.sleep(2)
                report.append({"pdf": str(path), **summarize(detail)})
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print(path.name, mode, detail["status"], flush=True)
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
