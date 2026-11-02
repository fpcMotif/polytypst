from collections.abc import Iterator, Sequence

from . import PageCheck
from .agents import Job, Runner, omp, run_agents

RUNBOOK = "docs/page-check.md"
MODEL = "gemini-3.8-flash"


def run(checks: Sequence[PageCheck], size: int, jobs: int, model: str, runner: Runner = omp) -> Iterator[str]:
    todo = []
    for check in checks:
        check.page_png(0).parent.mkdir(parents=True, exist_ok=True)
        for first, last in check.chunks(size):
            prompt = f"Follow this runbook with BOOK={check.key} FIRST={first} LAST={last}."
            todo.append(Job(prompt, check.root / "logs" / f"{check.key}_{first}-{last}.log"))
    yield f"{len(todo)} chunks, {jobs} at a time"
    for job, code in run_agents(RUNBOOK, todo, model, jobs, runner):
        tail = job.log.read_text(encoding="utf-8").strip().splitlines()[-1:] if job.log.exists() else []
        yield f"{job.log.stem}: exit {code}, {(tail or [''])[0][:120]}"
