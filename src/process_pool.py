import multiprocessing
import os
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor


def process_pool(jobs: int, initializer: Callable[..., None] | None = None, initargs: tuple = ()) -> ProcessPoolExecutor:
    context = multiprocessing.get_context("forkserver")
    context.set_forkserver_preload([__name__, *([initializer.__module__] if initializer else [])])
    return ProcessPoolExecutor(
        min(os.cpu_count() or 1, max(jobs, 1)), mp_context=context, initializer=_start, initargs=(initializer, initargs)
    )


def _start(initializer: Callable[..., None] | None, initargs: tuple) -> None:
    os.environ["RAYON_NUM_THREADS"] = "1"
    if initializer is not None:
        initializer(*initargs)
