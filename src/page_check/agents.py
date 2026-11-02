import subprocess
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

AGENT_TIMEOUT = 3600

type Runner = Callable[[str, str, str, Path], int]


@dataclass(frozen=True)
class Job:
    prompt: str
    log: Path


def omp(runbook: str, prompt: str, model: str, log: Path) -> int:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as out:
        return subprocess.run(
            ["omp", "-p", "--no-session", "--model", model, f"@{runbook}", prompt],
            stdout=out, stderr=subprocess.STDOUT, timeout=AGENT_TIMEOUT, check=False,
        ).returncode


def run_agents(
    runbook: str, jobs: Sequence[Job], model: str, parallel: int, runner: Runner = omp
) -> Iterator[tuple[Job, int]]:
    with ThreadPoolExecutor(parallel) as pool:
        yield from pool.map(lambda job: (job, runner(runbook, job.prompt, model, job.log)), jobs)
