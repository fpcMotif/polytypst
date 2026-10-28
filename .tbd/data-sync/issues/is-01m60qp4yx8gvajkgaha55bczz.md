---
type: is
id: is-01m60qp4yx8gvajkgaha55bczz
title: "polytypst profile: split build time by owner and time Typst cold, edited and repeat"
kind: feature
status: open
priority: 2
version: 1
labels:
  - ready-for-agent
dependencies: []
created_at: 2026-10-28T07:48:09.304Z
updated_at: 2026-10-28T07:48:09.304Z
---
## At a glance

Speed claims in polytypst came from a best-case benchmark: the Typst benchmark compiles one unchanged file three times, so it reported "15 to 60 times faster" when the real fit loop gained 1.5 times. The cause is that no command measures a build step as cold, edited and repeat runs, or says how much time Python spends against native libraries. A new `polytypst profile` command reports both, and it replaces the one-off Typst benchmark script. Build output, the Typst integration, and the Rust ink mask do not change.

## Problem Statement

As the maintainer, I ask "should this part move to Rust?" and get answers that contradict each other. In the native-speed session, the agent reported that embedded Typst made compiles and queries "15 to 60 times faster". The same session later found that a cold compile takes the same time from Python and from the Typst CLI (4.59–4.85 s against 4.85–4.95 s). The real `bourbaki_fit` run gained only 1.5 times (254.3 s → 169.6 s).

The 15–60× figure was accurate for one case only: the same `.typ` compiled again with nothing changed, so Typst's in-memory cache did all the work. The Typst benchmark measures only that case. It runs one cold CLI compile, then three embedded compiles of the unchanged source. A real workload changes the source between compiles, so most page layout runs again.

The second gap is where the time goes. The session ported code to Rust first. Later, while it checked the CPython JIT, it measured that Python bytecode is 3.6 s, about 6% of a build. The other 94% runs in MuPDF, numpy, Pillow and Typst. With that number in hand at the start, the agent would have known that a Rust rewrite of the glue code could save at most a few seconds. Each profiling round today is a hand-built `cProfile` command. One round failed because zsh did not split the argument string.

## Solution

`polytypst profile BOOK --edition E --step STEP` runs one build step of one edition under the profiler and prints two tables.

The first table splits the wall time by owner:
- Python bytecode
- each native library (MuPDF, numpy, Pillow, Typst, the Rust native module)
- waiting on subprocesses

It also lists the top functions by own time. The maintainer can see at once whether a Rust port could help. It can help only when Python bytecode or a Python-level loop is a large row.

For a step that compiles Typst, the second table times three labeled runs:
- `cold`: a new compiler instance with no cache
- `edited`: the same instance after a one-line change to the source
- `repeat`: the unchanged source compiled again

Each row says which case it measures, so a report cannot quote the repeat time as the speed of the step.

## User Stories

1. As the maintainer, I want one command that profiles a build step, so that I stop hand-writing `cProfile` commands.
2. As the maintainer, I want the profile to split time between Python bytecode and native libraries, so that I know whether Rust could help before anyone ports code.
3. As the maintainer, I want each native library named in the split, so that I can see that MuPDF rendering is the cost and not the language that calls it.
4. As the maintainer, I want time spent waiting on subprocesses shown as its own row, so that a CLI tool's start-up cost is visible.
5. As the maintainer, I want the top functions by own time, so that I can find a Python loop worth moving to Rust, like the ink mask was.
6. As the maintainer, I want the Typst step timed cold, edited and repeat, so that I see the speed a real fit loop gets.
7. As the maintainer, I want every timing row labeled with its case, so that a best-case number cannot pass as the typical one.
8. As the maintainer, I want the edited run to change the source the same way a fit round does, so that its time predicts the fit loop.
9. As the maintainer, I want to profile `build`, `parity` and `audit`, so that I can compare the checks as well as the build.
10. As the maintainer, I want the profile to leave my ink cache and outputs as they were, so that profiling does not change the next build.
11. As the maintainer, I want a cold run option that clears the ink cache in a scratch copy, so that I can measure a first build without losing my cache.
12. As the maintainer, I want the command to list its books and steps in `--help`, so that I do not need to read code to use it.
13. As an agent, I want a `polytypst profile` line in the book commands help, so that I find the command before I propose a port.
14. As an agent, I want the profile output as plain text tables, so that I can quote it in a report without a screenshot.
15. As an agent, I want a `--json` option, so that I can compare two profiles in a script.
16. As a reviewer, I want speed claims in a report to quote `polytypst profile` rows, so that I can check the claim's case and workload.
17. As the maintainer, I want the one-off Typst benchmark script removed, so that only one tool measures Typst and nobody reruns the warm-only version.
18. As the maintainer, I want the output-equality checks of the old Typst benchmark kept somewhere, so that I can still prove the embedded compiler matches the CLI.

## Implementation Decisions

- **New subcommand.** `profile` joins the book commands that `books_cli.main` dispatches. It takes the book key, `--edition`, `--step` (`build`, `parity` or `audit`), `--cold` and `--json`. The book commands help text gains one line for it.
- **Profiler.** The command runs the step in-process under `cProfile`. It groups functions by the file that owns them: the polytypst package and other pure-Python files count as Python bytecode, and calls into a compiled extension count toward that extension's library. Builtin calls into native modules (`pymupdf`, `numpy`, `PIL`, `polytypst_native`) are named by their module. `subprocess` waits get their own row.
- **Typst timings.** For a step that compiles Typst, the command times the edition's generated `.typ` three ways with the embedded `Typst` class: a new instance (`cold`), the same instance after a one-line change to a scratch copy of the source (`edited`), and the unchanged source again (`repeat`). The CLI time is printed beside `cold` for comparison.
- **Cold runs.** `--cold` runs the step against a scratch copy of the edition's ink cache folder, starting empty. The real cache is never moved or cleared.
- **Removed.** The one-off Typst benchmark script goes. Its PDF, query and PNG equality checks already live in the embedded Typst tests. Any check that is not covered there moves into those tests.
- **Unchanged.** The build steps, the embedded Typst integration, the CLI fallback, the Rust ink mask and the ink cache format stay as they are. ADR 0001 (Python 3.15 with the GIL) still holds.

## Testing Decisions

- A good test drives `books_cli.main("profile", [...])` and checks only its printed output and exit code. Tests do not check which profiler calls run inside.
- Prior art: `tests/test_cli.py` swaps in a probe `Book` through `monkeypatch` and calls `books_cli.main` directly. The profile tests use the same fixture style with a probe edition whose step calls a small Python loop, a numpy call and an embedded Typst compile.
- The tests check:
  - the owner table has Python, numpy and Typst rows
  - the Typst table has the three labeled rows, `cold`, `edited` and `repeat`
  - `--json` returns the same numbers as the text
  - `--cold` leaves the real ink cache folder byte-identical
- Timing values are not asserted, because they vary by machine. The tests assert labels, row presence and that the rows add up to the wall time within 5%.
- The embedded Typst tests keep their CLI-equality checks. They must still fail when the embedded compiler is switched off.

## Out of Scope

- Porting more code to Rust, including the FFT in `find_diagram` and the placement loops in `parity/words.py`.
- Changing the generated `.typ` to make Typst layout faster.
- A `CODING_STANDARDS.md` rule on speed claims, and a `docs/performance.md` page with the measured time breakdown. Both are docs work and need their own request.
- Performance checks in CI. Timings vary too much on shared runners.

## Further Notes

Evidence comes from session `5a897b49` on `explore/native-speed`:

| Measure | Result |
|---|---|
| Facsimile compile: CLI / embedded first / embedded repeat | 4.85 s / 4.59 s / 0.29 s |
| `bourbaki_fit`, 3 rounds: CLI / embedded | 254.3 s / 169.6 s |
| Python bytecode share of a build | 3.6 s, about 6% |
| Rust ink mask against numpy | 55 ms → 0.8 ms per page, identical output |
| Rust renderers against MuPDF on scans | `pylopdf` 12.8× slower, `pdf-oxide` 1.3–3.2× slower |
| Parity in a process pool | 123.9 s → 21.9 s, identical reports |

The rule these numbers support: profile first. Then fix the largest row with the cheapest tool, in this order: do less work, cache it, run it in parallel, and only then move a Python loop to Rust.
