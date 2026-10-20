"""`polytypst-colab`: see which Colab GPU fits which OCR model, probe GPUs, and benchmark them."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from itertools import product
from pathlib import Path

from .colab import COLAB_GPUS, account_usage, fit_problem, probe_gpu, write_probes
from .colab_cluster import benchmark
from .gpu_worker import page_items
from .ocr_models import DEFAULT_OCR_MODEL, OCR_MODELS


def _table(header: list[str], rows: list[list[str]]) -> str:
    widths = [max(len(r[i]) for r in [header, *rows]) for i in range(len(header))]
    lines = [header, ["-" * w for w in widths], *rows]
    return "\n".join(
        "  ".join(c.ljust(w) for c, w in zip(r, widths, strict=True)) for r in lines
    )


def show_gpus() -> None:
    header = ["GPU", "Card", "VRAM", "CU/hr", *OCR_MODELS]
    rows = []
    for gpu in COLAB_GPUS.values():
        cells = []
        for model in OCR_MODELS.values():
            problem = fit_problem(model, gpu)
            cells.append(
                "no" if problem else f"x{model.copies_per_gpu(gpu.vram_gb, 8)}"
            )
        rate = f"{gpu.cu_per_hour:.2f}" if gpu.cu_per_hour else "n/a"
        rows.append([gpu.name, gpu.card, f"{gpu.vram_gb:.0f} GB", rate, *cells])
    print(_table(header, rows))
    print("\nxN = model copies per GPU (vLLM models batch inside one copy).")
    for model in OCR_MODELS.values():
        prompt = "book prompt" if model.follows_book_prompt else "fixed prompt"
        print(
            f"  {model.key:<13} {model.hf_id:<32} {model.params_b:.1f}B  "
            f"~{model.vram_gb():.0f} GB  {model.runtime:<14} {prompt:<12} {model.license}"
        )


def show_usage() -> None:
    usage = account_usage()
    if usage is None:
        print("Colab CLI is missing or signed out. Run `colab usage` to check.")
        return
    print(
        f"Balance {usage.balance:.2f} CU | burn {usage.rate_per_hour:.2f} CU/hr | "
        f"{usage.active_assignments} active VM(s)"
    )


def run_probes(gpus: list[str], out: Path) -> None:
    probes = [probe_gpu(g) for g in gpus]
    write_probes(probes, out)
    rows = [
        [
            p.gpu,
            p.card or "-",
            f"{p.vram_gb:.1f}" if p.vram_gb else "-",
            str(p.compute_capability or "-"),
            f"{p.cu_per_hour:.2f}" if p.cu_per_hour is not None else "-",
            p.error or "ok",
        ]
        for p in probes
    ]
    print(_table(["GPU", "Card", "VRAM GB", "CC", "CU/hr", "Status"], rows))
    print(f"Wrote {out}")


def sample_pages(pages_dir: Path, count: int) -> list[Path]:
    """`count` renders spread evenly across the book, so the sample mixes prose and math."""
    items = [Path(p) for _, p in page_items(pages_dir)]
    if len(items) <= count:
        return items
    step = len(items) / count
    return [items[int(i * step + step / 2)] for i in range(count)]


def run_bench(
    gpus: list[str], models: list[str], pages_dir: Path, count: int, out: Path
) -> None:
    pages = sample_pages(pages_dir, count)
    combos = [
        (g, m)
        for g, m in product(gpus, models)
        if fit_problem(OCR_MODELS[m], COLAB_GPUS[g]) is None
    ]
    skipped = sorted(set(product(gpus, models)) - set(combos))
    for g, m in skipped:
        print(f"Skip {m} on {g}: {fit_problem(OCR_MODELS[m], COLAB_GPUS[g])}")
    with ThreadPoolExecutor(max_workers=max(1, len(combos))) as pool:
        results = list(
            pool.map(
                lambda c: benchmark(c[0], c[1], pages, out / f"{c[0]}_{c[1]}"), combos
            )
        )
    rows = [
        [
            r.gpu,
            r.model,
            f"{r.completed}/{r.pages}",
            f"{r.pages_per_sec:.3f}",
            f"{r.cu_per_1000_pages:.2f}" if r.cu_per_1000_pages else "-",
            f"{r.wall_sec:.0f}",
        ]
        for r in results
    ]
    print(_table(["GPU", "Model", "Pages", "Pages/s", "CU/1000 pages", "Wall s"], rows))
    out.mkdir(parents=True, exist_ok=True)
    report = out / "bench.json"
    _ = report.write_text(
        json.dumps(
            [
                {
                    **asdict(r),
                    "pages_per_sec": r.pages_per_sec,
                    "cu_per_1000_pages": r.cu_per_1000_pages,
                }
                for r in results
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Transcripts and {report.name} in {out}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="polytypst-colab", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    _ = sub.add_parser("gpus", help="GPU catalog and which OCR model fits each GPU")
    _ = sub.add_parser("usage", help="Compute-unit balance and burn rate")
    probe = sub.add_parser(
        "probe", help="Start each GPU briefly; record card, VRAM, CU/hr"
    )
    _ = probe.add_argument(
        "gpus", nargs="*", choices=sorted(COLAB_GPUS), default=sorted(COLAB_GPUS)
    )
    _ = probe.add_argument(
        "--out", type=Path, default=Path("output/colab_gpu_probes.json")
    )
    bench = sub.add_parser(
        "bench", help="Transcribe sample pages on every GPU x model pair"
    )
    _ = bench.add_argument(
        "pages_dir", type=Path, help="Directory of p_NNN.png renders"
    )
    _ = bench.add_argument(
        "--gpu", nargs="+", choices=sorted(COLAB_GPUS), default=["G4"]
    )
    _ = bench.add_argument(
        "--model", nargs="+", choices=sorted(OCR_MODELS), default=[DEFAULT_OCR_MODEL]
    )
    _ = bench.add_argument("--count", type=int, default=12)
    _ = bench.add_argument("--out", type=Path, default=Path("output/colab_bench"))
    args = parser.parse_args()
    if args.command == "gpus":
        show_gpus()
    elif args.command == "usage":
        show_usage()
    elif args.command == "probe":
        run_probes(args.gpus, args.out)
    else:
        run_bench(args.gpu, args.model, args.pages_dir, args.count, args.out)


if __name__ == "__main__":
    main()
