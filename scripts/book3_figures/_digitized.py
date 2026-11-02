from __future__ import annotations

import json
from pathlib import Path


def digitized(fig_id: str) -> list[tuple[float, float]]:
    """Points traced from the scan curve at its own time resolution (see each file's "method")."""
    data = json.loads((Path(__file__).parent / "digitized" / f"{fig_id}.json").read_text(encoding="utf-8"))
    return [(float(x), float(y)) for x, y in data["points"]]
