import logging
import threading
import time

from app.budget import BudgetExceeded, execution_budget
from app.config import settings
from app.db import Job, claim_job, event, heartbeat, init_db, now, session
from app.security import redact_credentials
from app.workflow import execute

log = logging.getLogger(__name__)


def run_once():
    claimed = claim_job()
    if not claimed:
        return False
    job_id, token = claimed
    stop = threading.Event()
    def keep_alive():
        while not stop.wait(20):
            heartbeat(job_id, token)
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    started = time.monotonic()
    try:
        with session() as db:
            available = settings().max_job_seconds - db.get(Job, job_id).elapsed_seconds
            if available <= 0:
                raise BudgetExceeded("Đã hết ngân sách thời gian xử lý job")
        with execution_budget(job_id, available):
            execute(job_id)
        with session() as db:
            job = db.get(Job, job_id)
            if job.lease_token == token:
                job.runnable = False
                job.pending_command = None
                job.error = None
    except Exception as exc:  # noqa: BLE001 -- checkpoint any failed node; sanitize before log/storage.
        safe_error = redact_credentials(exc)
        log.error("Job %s failed: %s", job_id, safe_error)
        with session() as db:
            job = db.get(Job, job_id)
            if job.lease_token == token:
                job.status = "failed"
                job.error = safe_error[:4000]
                job.runnable = False
        event(job_id, "failed", safe_error[:4000])
    finally:
        stop.set()
        thread.join(timeout=2)
        with session() as db:
            job = db.get(Job, job_id)
            if job.lease_token == token:
                job.elapsed_seconds += time.monotonic() - started
                job.updated_at = now()
                job.lease_until = None
                job.lease_token = None
    return True


def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    while True:
        if not run_once():
            time.sleep(1)


if __name__ == "__main__":
    main()
