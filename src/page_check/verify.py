import hashlib
import re
import subprocess
import unicodedata
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import cast

import pymupdf

from ..vision.figure_extractor import load_figures_manifest
from . import PageCheck, norm, ranges
from .agents import Job, Runner, omp, run_agents
from .lint import RUNNING_HEAD
from .render import caption_label, rebuilt_pages, scan_pages
from .results import (
    VERDICTS,
    Issue,
    IssueKey,
    Verdict,
    issue_key,
    read_jsonl,
    write_jsonl,
)
from .sheet import Strip, write_strips

NO_AUTO_VERDICT = {"sum", "table_shape"}
ZOOM_PAD = 0.02
ZOOM_DPI = 300
PAGE_DPI = 150
RUNBOOK = "docs/page-verify.md"
MODEL = "claude-sonnet-5-5"


def squash(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+(?=[^\x00-\x7f])|(?<=[^\x00-\x7f])\s+", "", text)


def auto_verdict(issue: Issue) -> str | None:
    """`false_positive` when the two sides differ only in character width or in spaces next to Chinese text.
    Spaces between Latin words and inside tags still count, so those issues go to a verifier."""
    t, s = issue.get("transcript", ""), issue.get("scan", "")
    if issue["kind"] in NO_AUTO_VERDICT or t == s or squash(t) != squash(s):
        return None
    return "false_positive"


def running_head_claim(issue: Issue, title: str) -> bool:
    """An `extra_text` claim on a page's running head. The page cleaner drops running heads, and `lint` finds any left in the built book."""
    head = issue.get("transcript", "").strip().lstrip("#").strip()
    return (
        issue["kind"] == "extra_text"
        and not issue.get("scan")
        and title in head
        and bool(RUNNING_HEAD.fullmatch(head))
    )


def zoom(check: PageCheck, issue: Issue, out: Path) -> Strip:
    """A 300 dpi strip of the scan around the issue's line, or the whole page when no OCR line holds its text."""
    page = int(issue["page"] or 0)
    texts = [t for t in (issue.get("scan", ""), issue.get("transcript", "")) if t]
    keys = [k for n in (12, 6, 3) for t in texts if len(norm(k := t[:n])) >= 2]
    found = next((b for key in keys if (b := check.band(page, key))), None)
    band = (max(0.0, found[0] - ZOOM_PAD), min(1.0, found[1] + ZOOM_PAD)) if found else (0.0, 1.0)
    return Strip(page, band, ZOOM_DPI if band != (0.0, 1.0) else PAGE_DPI, out)


def triage(check: PageCheck) -> tuple[int, int]:
    results = check.results
    folder = results.verify_folder
    folder.mkdir(parents=True, exist_ok=True)
    done = results.verdict_keys()
    lint_hits: list[Issue] = [{**h, "note": f"lint: {h['rule']}"} for h in results.lint_hits() if h["page"]]
    pending = [i for i in [*results.page_issues(), *lint_hits] if issue_key(i) not in done]
    settled: list[Verdict] = []
    open_claims: list[Issue] = []
    for issue in pending:
        if auto_verdict(issue):
            settled.append({**issue, "verdict": "false_positive", "detail": "width or spacing only", "by": "auto"})
        elif running_head_claim(issue, check.title):
            settled.append({**issue, "verdict": "false_positive", "detail": "running head, which the build drops", "by": "auto"})
        else:
            open_claims.append(issue)
    results.add_verdicts(settled)
    page_images = {p: folder / f"page{p}.png" for p in sorted({int(i["page"] or 0) for i in open_claims})}
    zooms = [zoom(check, issue, folder / f"p{issue['page']}_{k}.png") for k, issue in enumerate(open_claims)]
    pages = [Strip(p, (0.0, 1.0), PAGE_DPI, path) for p, path in page_images.items() if not path.exists()]
    if open_claims:
        write_strips(check.scan_doc, pages + zooms)
    queue: list[Issue] = [
        {**issue, "zoom": str(z.out), "page_image": str(page_images[int(issue["page"] or 0)])}
        for issue, z in zip(open_claims, zooms, strict=True)
    ]
    results.write_queue(queue)
    return len(settled), len(queue)


def verify(check: PageCheck, size: int, jobs: int, model: str, runner: Runner = omp) -> Iterator[str]:
    """Start one agent for each batch of queued issues, then add their verdicts to verdicts.jsonl. A batch whose
    output exists is not run again, so a rerun only starts the batches that failed."""
    results = check.results
    folder = results.verify_folder
    done = results.verdict_keys()
    queue = [q for q in results.queue() if issue_key(q) not in done]
    batches: list[tuple[Path, Path]] = []
    for i in range(0, len(queue), size):
        part = queue[i : i + size]
        name = hashlib.sha1(repr([issue_key(q) for q in part]).encode()).hexdigest()[:8]
        items, out = folder / f"q{name}.jsonl", folder / f"v{name}.jsonl"
        write_jsonl(items, part)
        batches.append((items, out))
    todo = {out.with_suffix(".log"): (items, out) for items, out in batches if not out.exists()}
    yield f"{len(queue)} issues, {len(todo)} of {len(batches)} batches to run, {jobs} at a time"
    agent_jobs = [Job(f"Follow this runbook with ITEMS={items} OUT={out}.", log) for log, (items, out) in todo.items()]
    for job, code in run_agents(RUNBOOK, agent_jobs, model, jobs, runner):
        items, out = todo[job.log]
        report = f"{out.name}: exit {code}, {len(read_jsonl(out))} of {len(read_jsonl(items))} verdicts"
        if code:
            tail = job.log.read_text(encoding="utf-8").strip().splitlines()[-3:] if job.log.exists() else []
            report += "; log tail: " + " | ".join(tail)
        yield report
    queued = {issue_key(q): q for q in queue}
    added: list[Verdict] = []
    for _, out in batches:
        for v in read_jsonl(out):
            key = issue_key(v)
            if key in queued and key not in done and v.get("verdict") in VERDICTS:
                done.add(key)
                q = queued[key]
                kept = {k: q[k] for k in ("page", "line", "kind", "transcript", "scan") if k in q}
                added.append(cast(Verdict, kept | {"verdict": v["verdict"], "detail": v.get("detail", ""), "by": model}))
    results.add_verdicts(added)
    yield f"{len(added)} verdicts added"


def unverified_issues(check: PageCheck) -> set[IssueKey]:
    results = check.results
    claims = [*results.page_issues(), *(h for h in results.lint_hits() if h["page"])]
    return {issue_key(i) for i in claims} - results.verdict_keys()


def audit(check: PageCheck) -> tuple[int, str]:
    """The exit code and the last output line of `polytypst audit` for the book."""
    done = subprocess.run(["polytypst", "audit", check.key], capture_output=True, text=True, check=False)
    lines = (done.stdout + done.stderr).strip().splitlines()
    return done.returncode, lines[-1] if lines else ""


def figure_labels(captions: Iterable[str]) -> set[str]:
    return {label for caption in captions if (label := caption_label(caption)) and label.startswith(("图", "Figure"))}


def gate(check: PageCheck, pdf: Path | None, manifest: Path) -> list[str]:
    """One line per check, each PASS, WARN or FAIL, then PASS only when no check fails."""
    lines = []

    def passes(ok: bool, text: str) -> None:
        lines.append(f"{'PASS' if ok else 'FAIL'} {text}")

    t = check.tally()
    missing = sorted(t.pages - t.checked)
    passes(
        not missing,
        f"page check: {len(t.checked & t.pages)}/{len(t.pages)} pages with a valid receipt"
        + (f", missing {ranges(missing)}" if missing else ""),
    )
    issues = len(check.results.page_issues())
    if not issues and len(t.pages) > 100:
        lines.append(f"WARN page check: 0 issues from {len(t.pages)} pages; open five pages beside their scans and compare them")
    linted = check.results.linted()
    passes(linted, "lint: run" if linted else f"lint: not run; run `polytypst page-check lint {check.key}`")
    unverified = unverified_issues(check)
    passes(not unverified, f"verdicts: {issues} issues, {len(unverified)} unverified")
    scan = {label for label in scan_pages(check) if label.startswith(("图", "Figure"))}
    listed = figure_labels(f.caption for f in load_figures_manifest(manifest)) if manifest.exists() else set()
    absent = sorted(scan - listed)
    passes(
        not absent,
        f"figures: {len(scan)} figure captions in the scan"
        + (f", not in {manifest}: {', '.join(absent)}" if absent else ", all in the manifest"),
    )
    if pdf is None or not pdf.exists():
        passes(False, f"figures: no rebuilt PDF at {pdf}; build the book first")
    else:
        dropped = sorted(scan - set(rebuilt_pages(pymupdf.open(pdf))))
        passes(
            not dropped,
            "figures: " + (f"not in the rebuilt PDF {pdf}: {', '.join(dropped)}" if dropped else "all in the rebuilt PDF"),
        )
    code, last = audit(check)
    passes(code == 0, f"audit: exit {code}, {last}")
    failed = sum(line.startswith("FAIL") for line in lines)
    checks = sum(line.startswith(("PASS", "FAIL")) for line in lines)
    return [*lines, f"FAIL: {failed} of {checks} checks" if failed else "PASS"]


def status(check: PageCheck) -> list[str]:
    results = check.results
    t = check.tally()
    lint_hits = results.lint_hits()
    claims = [*results.page_issues(), *(h for h in lint_hits if h["page"])]
    verdicts = results.verdicts()
    unverified = unverified_issues(check)
    queued = {issue_key(q) for q in results.queue()}
    by = Counter(v["verdict"] for v in verdicts)
    judged = sum(n for k, n in by.items() if k != "sum")
    lines = [
        f"book {check.key}",
        f"  page check: {len(t.checked & t.pages)}/{len(t.pages)} pages, {len(claims) - len(lint_hits)} issues",
        f"  lint: {dict(Counter(h.get('rule') for h in lint_hits)) if results.linted() else 'not run'}",
        f"  verdicts: {dict(by)}, {sum(v.get('by') == 'auto' for v in verdicts)} auto, {len(unverified)} unverified"
        + (f", false-positive rate {by['false_positive'] / judged:.0%}" if judged else ""),
        f"  false negatives: {len(results.false_negatives())}",
    ]
    steps = []
    if missing := sorted(t.pages - t.checked):
        steps.append(f"polytypst page-check run {check.key}   # unchecked {ranges(missing)}")
    if not results.linted():
        steps.append(f"polytypst page-check lint {check.key}")
    if unverified - queued:
        steps.append(f"polytypst page-check triage {check.key}")
    elif unverified:
        steps.append(f"polytypst page-check verify {check.key}")
    if by["real"] or by["scan_typo"]:
        steps.append("fix the real and scan_typo verdicts: docs/page-check-review.md, Step 4")
    return [*lines, *(f"  next: {s}" for s in steps)]
