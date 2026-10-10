import time
from contextlib import contextmanager

DEADLINES: dict[str, float] = {}


class BudgetExceeded(RuntimeError):
    pass


def remaining_seconds(job_id: str, default=360):
    remaining = DEADLINES.get(job_id, time.monotonic() + default) - time.monotonic()
    if remaining <= 0:
        raise BudgetExceeded("Đã hết ngân sách thời gian xử lý job; checkpoint được giữ lại.")
    return min(default, remaining)


@contextmanager
def execution_budget(job_id: str, seconds: float):
    DEADLINES[job_id] = time.monotonic() + seconds
    try:
        yield
    finally:
        DEADLINES.pop(job_id, None)
