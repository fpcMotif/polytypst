import json
import re
from pathlib import Path

from polytypst.book_state import book_state

source_ocr_dir = book_state(Path("output/functional_analysis")) / "source_ocr"
md_dir = book_state(Path("output/functional_analysis")) / "markdown_pages"

flagged: list[tuple[int, str, float, int, list[str]]] = []
total_pages = 478
coverages: list[float] = []

for pno in range(1, total_pages + 1):
    json_path = source_ocr_dir / f"p{pno:03d}.json"
    md_path = md_dir / f"p_{pno:03d}.md"

    if not json_path.exists():
        continue
    if not md_path.exists():
        continue

    ocr_lines: list[dict[str, object]] = json.loads(json_path.read_text(encoding="utf-8"))
    ocr_text = " ".join(str(l.get("text", "")) for l in ocr_lines).strip()
    md_text = md_path.read_text(encoding="utf-8").strip()

    # extract words of length >= 3
    ocr_words = set(re.findall(r"\b[A-Za-z]{3,}\b", ocr_text.lower()))
    md_words = set(re.findall(r"\b[A-Za-z]{3,}\b", md_text.lower()))

    if not ocr_words:
        continue

    overlap = len(ocr_words & md_words)
    cov = overlap / len(ocr_words)
    coverages.append(cov)

    if cov < 0.75:
        missing = sorted(ocr_words - md_words)[:10]
        flagged.append((pno, "LOW_WORD_COVERAGE", cov, len(ocr_words), missing))

avg_cov = sum(coverages) / len(coverages) if coverages else 0.0
print(f"Total pages audited: {len(coverages)}")
print(f"Mean page word coverage: {avg_cov * 100:.2f}%")
print(f"Pages with word coverage < 75%: {len(flagged)}")
for item in flagged:
    pno, reason, cov, w_count, missing = item
    print(f"  Page {pno:03d}: {cov * 100:.1f}% coverage ({w_count} words). Missing sample: {missing}")
