import time
from pathlib import Path

import pytest

from polytypst.ocr.apple_vision import AppleVisionReader
from polytypst.ocr.pages import OcrLine, OcrStalled, PageImage

STALLING_RUNNER = """#!/bin/sh
printf '{"page": 1, "lines": [{"text": "done", "x": 0.1, "y": 0.2, "w": 0.3, "h": 0.04}]}' > "$2/page_0001.json"
sleep 30
"""


def test_a_runner_that_stops_writing_is_killed_after_the_lines_it_wrote(tmp_path: Path) -> None:
    runner = tmp_path / "runner"
    runner.write_text(STALLING_RUNNER)
    runner.chmod(0o755)
    images = [PageImage(n, tmp_path / f"fig_{n}.png") for n in (1, 2)]
    for image in images:
        image.path.write_bytes(b"png")
    reader = AppleVisionReader(["en-US"], stall_seconds=1.0)
    reader._compiled_binary = runner

    started, read = time.monotonic(), []
    with pytest.raises(OcrStalled):
        read.extend(reader.read(images))

    assert time.monotonic() - started < 10
    assert [(p.number, p.lines) for p in read] == [(1, (OcrLine("done", 0.1, 0.2, 0.3, 0.04),))]
