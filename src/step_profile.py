"""`polytypst profile`: where a build step spends its time, and how fast Typst compiles cold, edited and repeat."""

import cProfile
import pstats
import re
import subprocess
import tempfile
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from polytypst_native import Typst

from .compiler.typst_math import REPO_FONTS_DIR, typst_command
from .parity.ink_cache import InkCache

PYTHON = "Python bytecode"
SUBPROCESS = "subprocess wait"
WORKER_FILES = ("/subprocess.py", "/multiprocessing/", "/concurrent/futures/")
RELAY_FILES = ("/selectors.py", "/threading.py")
RELAY_DEPTH = 3
OTHER_NATIVE = "other builtins"
TOP_FUNCTIONS = 15
NATIVE_OWNERS = (
    ("builtins.Typst", "Typst"),
    ("polytypst_native.Typst", "Typst"),
    ("polytypst_native", "polytypst_native (Rust)"),
    ("pymupdf", "MuPDF"),
    ("_mupdf", "MuPDF"),
    ("mupdf", "MuPDF"),
    ("numpy", "numpy"),
    ("PIL", "Pillow"),
    ("ImagingCore", "Pillow"),
)
WRAPPER_OWNERS = (("/site-packages/numpy/", "numpy"), ("/site-packages/pymupdf/", "MuPDF"), ("/site-packages/PIL/", "Pillow"))
_BUILTIN_MODULE = re.compile(
    r"<built-in method ([\w.]+?)\.\w+>|<method '\w+' of '([\w.]+)' objects>|<built-in method \w+ of ([\w.]+) object"
)
_LENGTH = re.compile(r"\d+\.\d+(?=pt|mm|cm|em|%)")

type FunctionKey = tuple[str, int, str]
type CallTimes = tuple[int, int, float, float]
type Stats = dict[FunctionKey, tuple[int, int, float, float, dict[FunctionKey, CallTimes]]]


@dataclass(frozen=True)
class OwnerTime:
    owner: str
    seconds: float
    share: float


@dataclass(frozen=True)
class FunctionTime:
    function: str
    owner: str
    calls: int
    seconds: float


@dataclass(frozen=True)
class TypstTime:
    case: str
    seconds: float
    measures: str


@dataclass(frozen=True)
class StepProfile:
    title: str
    exit_code: int
    wall: float
    owners: list[OwnerTime]
    functions: list[FunctionTime]
    typst: list[TypstTime]


def native_owner(label: str) -> str:
    """The library behind a builtin's cProfile label, such as "<method 'compile' of 'polytypst_native.Typst' objects>"."""
    match = _BUILTIN_MODULE.search(label)
    module = next((g for g in match.groups() if g), "") if match else ""
    for prefix, owner in NATIVE_OWNERS:
        if module == prefix or module.startswith(f"{prefix}."):
            return owner
    return OTHER_NATIVE


def python_owner(path: str) -> str:
    """A native library's own Python wrappers count toward the library: cProfile folds the C calls it cannot see, such as
    numpy's ufuncs and LAPACK, into the Python frame that made them."""
    return next((owner for part, owner in WRAPPER_OWNERS if part in path), PYTHON)


def _waits_on_workers(stats: Stats, caller: FunctionKey, depth: int) -> bool:
    """Whether a builtin called from `caller` waits on a subprocess or pool worker, looking up through relays such as
    selectors.py, which subprocess.communicate calls to poll its pipes."""
    path = caller[0]
    if any(part in path for part in WORKER_FILES):
        return True
    if depth == 0 or not any(path.endswith(relay) for relay in RELAY_FILES) or caller not in stats:
        return False
    _, _, _, _, up = stats[caller]
    return any(_waits_on_workers(stats, key, depth - 1) for key in up)


def _waited(stats: Stats, own: float, callers: dict[FunctionKey, CallTimes]) -> float:
    """The part of a builtin's `own` time spent waiting on workers. cProfile can record a caller's share as zero, so the
    split follows the recorded shares, and with none recorded a wait needs every caller to be waiting."""
    waiting = {caller: _waits_on_workers(stats, caller, RELAY_DEPTH) for caller in callers}
    shares = {caller: own_time for caller, (_, _, own_time, _) in callers.items()}
    recorded = sum(shares.values())
    if recorded > 0:
        return own * sum(s for caller, s in shares.items() if waiting[caller]) / recorded
    return own if waiting and all(waiting.values()) else 0.0


def _timed[T](run: Callable[[], T]) -> tuple[float, T]:
    start = time.perf_counter()
    result = run()
    return time.perf_counter() - start, result


def profile_step(title: str, run: Callable[[], int]) -> StepProfile:
    """Run `run` under cProfile and split its own time: Python files, each native library, and waits on workers."""
    profiler = cProfile.Profile()
    wall, exit_code = _timed(lambda: profiler.runcall(run))
    stats: Stats = vars(pstats.Stats(profiler))["stats"]
    owners: Counter[str] = Counter()
    functions = []
    for (path, line, name), (_, calls, own, _, callers) in stats.items():
        if path != "~":
            owner = python_owner(path)
            owners[owner] += own
        else:
            waited = _waited(stats, own, callers)
            native = native_owner(name)
            owners[SUBPROCESS] += waited
            owners[native] += own - waited
            owner = SUBPROCESS if waited > own / 2 else native
        label = name if path == "~" else f"{Path(path).name}:{line}({name})"
        functions.append(FunctionTime(label, owner, calls, own))
    functions.sort(key=lambda f: -f.seconds)
    total = owners.total() or 1.0
    shares = [OwnerTime(o, s, s / total) for o, s in owners.most_common()]
    return StepProfile(title, exit_code, wall, shares, functions[:TOP_FUNCTIONS], [])


def edit_one_line(text: str) -> str:
    """Move the length nearest the middle of the source by 0.1, as a fit round moves one placement."""
    lengths = list(_LENGTH.finditer(text))
    if not lengths:
        return f"{text}\n#v(0pt)\n"
    middle = min(lengths, key=lambda m: abs(m.start() - len(text) // 2))
    moved = f"{float(middle.group()) + 0.1:.{len(middle.group().split('.')[1])}f}"
    return f"{text[: middle.start()]}{moved}{text[middle.end() :]}"


def time_typst(typ: Path) -> list[TypstTime]:
    """Compile a scratch copy of `typ` beside it: a new instance, after a one-line edit, then unchanged; and once by the CLI."""
    scratch = typ.with_name(f".profile_{typ.name}")
    text = typ.read_text(encoding="utf-8")
    scratch.write_text(text, encoding="utf-8")
    try:
        cold, typst = _timed(lambda: _compiled(Typst([str(REPO_FONTS_DIR)]), scratch))
        scratch.write_text(edit_one_line(text), encoding="utf-8")
        edited, _ = _timed(lambda: _compiled(typst, scratch))
        repeat, _ = _timed(lambda: _compiled(typst, scratch))
        scratch.write_text(text, encoding="utf-8")
        cli = _time_cli(scratch)
    finally:
        scratch.unlink()
    return [
        TypstTime("cold", cold, "new compiler instance with its font scan, no cache"),
        TypstTime("edited", edited, "same instance after a one-line change, like a fit round"),
        TypstTime("repeat", repeat, "unchanged source again: the cache's best case, not a step's speed"),
        *([TypstTime("cli", cli, "typst compile, to compare with cold")] if cli is not None else []),
    ]


def _compiled(typst: Typst, typ: Path) -> Typst:
    _ = typst.compile(str(typ), root="/")
    return typst


def _time_cli(typ: Path) -> float | None:
    command = typst_command(fallback_nix=False)
    if command is None:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        argv = [*command, "compile", "--font-path", str(REPO_FONTS_DIR), "--root", "/", str(typ), str(Path(tmp) / "cli.pdf")]
        seconds, done = _timed(lambda: subprocess.run(argv, capture_output=True, check=False))
    return seconds if done.returncode == 0 else None


def run_cold[T](run: Callable[[], T]) -> T:
    """Run with every ink cache in an empty scratch folder, as a first build draws it; the real cache is left as it is."""
    with tempfile.TemporaryDirectory() as tmp:
        InkCache.scratch = Path(tmp)
        try:
            return run()
        finally:
            InkCache.scratch = None


def render(profile: StepProfile) -> str:
    total = sum(o.seconds for o in profile.owners)
    lines = [
        f"{profile.title}: exit {profile.exit_code}, wall {profile.wall:.2f} s, profiled {total:.2f} s",
        "",
        "time by owner",
        f"{'OWNER':<24}{'SECONDS':>9}{'SHARE':>7}",
        *(f"{o.owner:<24}{o.seconds:>9.2f}{o.share:>7.0%}" for o in profile.owners),
        "",
        "top functions by own time",
        f"{'SECONDS':>9}{'CALLS':>9}  {'OWNER':<24}FUNCTION",
        *(f"{f.seconds:>9.3f}{f.calls:>9}  {f.owner:<24}{f.function}" for f in profile.functions),
    ]
    if profile.typst:
        lines += ["", "Typst compile of the generated .typ", f"{'CASE':<8}{'SECONDS':>9}  MEASURES"]
        lines += [f"{t.case:<8}{t.seconds:>9.2f}  {t.measures}" for t in profile.typst]
    return "\n".join(lines)


def as_json(profile: StepProfile) -> dict[str, object]:
    return asdict(profile)
