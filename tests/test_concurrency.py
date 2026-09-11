import threading
import time

import pytest

from app.concurrency import ConcurrentProcessor


def test_process_batch_runs_items_in_parallel_and_preserves_order():
    processor = ConcurrentProcessor(max_workers=2)
    active = 0
    peak = 0
    lock = threading.Lock()

    def process(item):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        return item * 2

    try:
        assert processor.process_batch([1, 2, 3], process) == [2, 4, 6]
        assert peak == 2
    finally:
        processor.shutdown()


def test_process_batch_rejects_invalid_worker_count():
    with pytest.raises(ValueError, match="at least 1"):
        ConcurrentProcessor(max_workers=0)
