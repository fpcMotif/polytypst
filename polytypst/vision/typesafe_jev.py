"""TypeSafe Jev 1.14 vision grounding engine using Box and Noul primitives."""

import base64
import io
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np
from PIL import Image


@dataclass
class DiagramDetectionResult:
    has_diagram: bool
    noul_score: float
    box: tuple[float, float, float, float] | None = (
        None  # (left, top, right, bottom) in normalized coords
    )
    caption_box: tuple[float, float, float, float] | None = None
    confidence: float = 0.0


class TypeSafeJevVision:
    def __init__(self, api_key: str | None = None, model: str = "jev-preview") -> None:
        self.api_key: str | None = api_key or os.environ.get("TYPESAFE_API_KEY")
        if not self.api_key:
            # Check default path from jev-ultrafast if present
            default_env = Path.home() / "devv" / "jev-ultrafast" / ".env"
            if default_env.exists():
                with open(default_env) as f:
                    for line in f:
                        if line.startswith("TYPESAFE_API_KEY="):
                            self.api_key = line.strip().split("=", 1)[1]
                            break

        self.model: str = model
        self.endpoint: str = "https://api.typesafe.ai/v1/systemone"

    def detect_diagram(
        self, image_path: Path, fig_label: str | None = None
    ) -> DiagramDetectionResult:
        """Evaluate if an image contains a diagram, chart, or flowchart, and return its bounding box."""
        if not self.api_key:
            return DiagramDetectionResult(has_diagram=False, noul_score=0.0)

        # Scale down for fast network transport
        img = Image.open(image_path)
        max_dim = 1200
        if max(img.width, img.height) > max_dim:
            scale = max_dim / max(img.width, img.height)
            img = img.resize(
                (int(img.width * scale), int(img.height * scale)),
                Image.Resampling.LANCZOS,
            )

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64_data = base64.b64encode(buf.getvalue()).decode("ascii")

        diag_inst = (
            f"the mathematical geometric diagram or figure drawing for {fig_label} itself (excluding its '{fig_label}' caption text below it) in `page`"
            if fig_label
            else "the mathematical geometric diagram or figure drawing itself (excluding its FIG. caption text below it) in `page`"
        )
        cap_inst = (
            f"the printed caption line starting with '{fig_label}' below the diagram in `page`"
            if fig_label
            else "the printed caption line starting with 'FIG.' below the diagram in `page`"
        )

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
                    "instructions": "Is there a diagram, flowchart, graph, or organizational model drawing on this `page`?",
                },
                "diagram_box": {
                    "type": "box",
                    "instructions": diag_inst,
                },
                "caption_box": {
                    "type": "box",
                    "instructions": cap_inst,
                },
            },
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "TypeSafe-Danger-Zone-Images": "true",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(self.endpoint, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            answers = data.get("answers", {})
            noul_ans = answers.get("has_diagram", {})
            noul_score = float(noul_ans.get("noul", 0.0))

            box_ans = answers.get("diagram_box", {})
            box_edges = box_ans.get("box", {})
            conf = float(box_ans.get("confidence", 0.0))

            cap_ans = answers.get("caption_box", {})
            cap_edges = cap_ans.get("box", {})

            has_diag = noul_score >= 0.70
            box_coords: tuple[float, float, float, float] | None = None
            if has_diag and box_edges:
                box_coords = (
                    float(box_edges.get("left", 0.0)),
                    float(box_edges.get("top", 0.0)),
                    float(box_edges.get("right", 1.0)),
                    float(box_edges.get("bottom", 1.0)),
                )

            cap_coords: tuple[float, float, float, float] | None = None
            if cap_edges:
                cap_coords = (
                    float(cap_edges.get("left", 0.0)),
                    float(cap_edges.get("top", 0.0)),
                    float(cap_edges.get("right", 1.0)),
                    float(cap_edges.get("bottom", 1.0)),
                )

            return DiagramDetectionResult(
                has_diagram=has_diag,
                noul_score=noul_score,
                box=box_coords,
                caption_box=cap_coords,
                confidence=conf,
            )
        except (httpx.HTTPError, OSError, ValueError, KeyError) as e:
            print(f"TypeSafe Jev vision call failed: {e}")
            return DiagramDetectionResult(has_diagram=False, noul_score=0.0)

    @staticmethod
    def crop_pure_diagram(
        image_path: Path,
        detection: DiagramDetectionResult,
        out_path: Path,
        pad_px: int = 16,
    ) -> Path:
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        dbox = detection.box or (0.08, 0.08, 0.92, 0.85)
        cbox = detection.caption_box

        left = max(0.0, dbox[0] - 0.015)
        right = min(1.0, dbox[2] + 0.015)
        top = max(0.0, dbox[1] - 0.015)
        bottom = min(1.0, dbox[3] + 0.010)
        if cbox and cbox[1] > top + 0.04:
            bottom = min(bottom, cbox[1] - 0.008)

        x0, y0 = int(left * w), int(top * h)
        x1, y1 = int(right * w), int(bottom * h)
        crop = img.crop((x0, y0, x1, y1))

        arr = np.array(crop.convert("L"))
        ink = arr < 215
        ch, cw = ink.shape
        border = max(4, int(min(ch, cw) * 0.01))
        ink[:border, :] = False
        ink[-border:, :] = False
        ink[:, :border] = False
        ink[:, -border:] = False

        row_ink = ink.sum(axis=1)
        is_blank = row_ink <= 2
        bands: list[tuple[int, int]] = []
        in_band = False
        start_r = 0
        for r, b_val in enumerate(is_blank):
            if b_val and not in_band:
                in_band = True
                start_r = r
            elif not b_val and in_band:
                in_band = False
                if r - start_r >= 10:
                    bands.append((start_r, r))
        if in_band and ch - start_r >= 10:
            bands.append((start_r, ch))

        for b_start, b_end in reversed(bands):
            if b_start > ch * 0.68:
                below_ink = ink[b_end:, :]
                if below_ink.shape[0] < ch * 0.20:
                    ink[b_start:, :] = False

        for b_start, b_end in bands:
            if b_end < ch * 0.25 and b_start < ch * 0.18:
                ink[:b_end, :] = False

        ys, xs = np.where(ink)
        if len(ys) > 20:
            ymin = max(0, int(ys.min()) - pad_px)
            ymax = min(crop.height, int(ys.max()) + pad_px)
            xmin = max(0, int(xs.min()) - pad_px)
            xmax = min(crop.width, int(xs.max()) + pad_px)
            crop = crop.crop((xmin, ymin, xmax, ymax))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        crop.save(out_path)
        return out_path
