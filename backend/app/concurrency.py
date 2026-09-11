from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, List, TypeVar


Item = TypeVar("Item")
Result = TypeVar("Result")


class ConcurrentProcessor:
    """Process independent items in a bounded pool, preserving input order."""

    def __init__(self, max_workers: int = 4):
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="label-worker",
        )

    def process_batch(
        self,
        items: Iterable[Item],
        processor: Callable[[Item], Result],
    ) -> List[Result]:
        return list(self._executor.map(processor, items))

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True)
