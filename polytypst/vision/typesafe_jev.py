"""TypeSafe Jev 1.14 vision grounding engine using Box and Noul primitives."""

import base64
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
import httpx
from PIL import Image


@dataclass
class DiagramDetectionResult:
    has_diagram: bool
    noul_score: float
    box: Optional[Tuple[float, float, float, float]] = None  # (left, top, right, bottom) in normalized coords
    confidence: float = 0.0


class TypeSafeJevVision:
    def __init__(self, api_key: Optional[str] = None, model: str = "jev-preview"):
        self.api_key = api_key or os.environ.get("TYPESAFE_API_KEY")
        if not self.api_key:
            # Check default path from jev-ultrafast if present
            default_env = Path.home() / "devv" / "jev-ultrafast" / ".env"
            if default_env.exists():
                with open(default_env) as f:
                    for line in f:
                        if line.startswith("TYPESAFE_API_KEY="):
                            self.api_key = line.strip().split("=", 1)[1]
                            break

        self.model = model
        self.endpoint = "https://api.typesafe.ai/v1/systemone"

    def detect_diagram(self, image_path: Path) -> DiagramDetectionResult:
        """Evaluate if an image contains a diagram, chart, or flowchart, and return its bounding box."""
        if not self.api_key:
            return DiagramDetectionResult(has_diagram=False, noul_score=0.0)

        # Scale down for fast network transport
        img = Image.open(image_path)
        max_dim = 1200
        if max(img.width, img.height) > max_dim:
            scale = max_dim / max(img.width, img.height)
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)

        import io
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64_data = base64.b64encode(buf.getvalue()).decode("ascii")

        asset_id = str(uuid.uuid4())
        payload = {
            "model": self.model,
            "state": {"page": asset_id},
            "assets": {
                asset_id: {"type": "image", "format": "jpg", "data_base64": b64_data}
            },
            "questions": {
                "has_diagram": {
                    "type": "noul",
                    "instructions": "Is there a diagram, flowchart, graph, or organizational model drawing on this `page`?"
                },
                "diagram_box": {
                    "type": "box",
                    "instructions": "the diagram, flowchart, or chart drawing in `page`"
                }
            }
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "TypeSafe-Danger-Zone-Images": "true",
            "Content-Type": "application/json"
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(self.endpoint, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            answers = data.get("answers", {})
            noul_ans = answers.get("has_diagram", {})
            noul_score = noul_ans.get("noul", 0.0)

            box_ans = answers.get("diagram_box", {})
            box_edges = box_ans.get("box", {})
            conf = box_ans.get("confidence", 0.0)

            has_diag = noul_score >= 0.70
            box_coords = None
            if has_diag and box_edges:
                box_coords = (
                    box_edges.get("left", 0.0),
                    box_edges.get("top", 0.0),
                    box_edges.get("right", 1.0),
                    box_edges.get("bottom", 1.0)
                )

            return DiagramDetectionResult(
                has_diagram=has_diag,
                noul_score=noul_score,
                box=box_coords,
                confidence=conf
            )
        except Exception as e:
            print(f"TypeSafe Jev vision call failed: {e}")
            return DiagramDetectionResult(has_diagram=False, noul_score=0.0)
