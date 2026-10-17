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

    CAPTION_TOKEN_RE = (
        r"(?i)(?:fig|figure|fio|fia|fiq|f1g|f10|pig|pi0|pio|fg|flc|flo|ıo|abbildung|图)"
        r"\s*[\.,]?\s*(?:\d+|[sS]\b)"
    )

    @staticmethod
    def crop_pure_diagram(
        image_path: Path,
        detection: DiagramDetectionResult,
        out_path: Path,
        pad_px: int = 16,
        ocr_lines: list[object] | None = None,
    ) -> Path:
        import re
        import tempfile

        from ..ocr.apple_vision import AppleVisionOCREngine
        from ..ocr.base import OCRLine

        cap_re = re.compile(TypeSafeJevVision.CAPTION_TOKEN_RE)
        eng = AppleVisionOCREngine(languages=["en-US"])
        lines: list[OCRLine] = []
        if ocr_lines is not None:
            lines = [l for l in ocr_lines if isinstance(l, OCRLine)]
        else:
            try:
                lines = eng.recognize_page(image_path, 1).lines
            except (OSError, RuntimeError, ValueError):
                lines = []

        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        arr = np.array(img)
        dbox = detection.box or (0.08, 0.08, 0.92, 0.85)
        diag_cx = (dbox[0] + dbox[2]) / 2.0
        diag_top = dbox[1]
        diag_bot = dbox[3]

        right_col_xs = [
            l.x
            for l in lines
            if l.w > 0.16
            and l.x > 0.42
            and (1.0 - l.y) > diag_top - 0.05
            and (1.0 - (l.y + l.h)) < diag_bot + 0.05
        ]
        left_col_rights = [
            l.x + l.w
            for l in lines
            if l.w > 0.16
            and (l.x + l.w) < 0.62
            and (1.0 - l.y) > diag_top - 0.05
            and (1.0 - (l.y + l.h)) < diag_bot + 0.05
        ]
        x_right_col = min(right_col_xs) if (diag_cx < 0.48 and len(right_col_xs) >= 3) else 1.0
        x_left_col = max(left_col_rights) if (diag_cx > 0.52 and len(left_col_rights) >= 3) else 0.0

        for l in lines:
            txt = l.text.strip()
            l_top = 1.0 - (l.y + l.h)
            l_bot = 1.0 - l.y
            is_cap = bool(cap_re.search(txt)) and l.w < 0.32
            is_header_footer = l_top < 0.115 or l_bot > 0.90
            is_prose = l.w > 0.16 or len(txt.split()) >= 3 or len(txt) >= 10
            is_side_col = (l.x >= x_right_col - 0.012) or ((l.x + l.w) <= x_left_col + 0.012)
            if is_cap or is_header_footer or is_prose or is_side_col:
                px0 = max(0, int((l.x - 0.004) * w))
                px1 = min(w, int((l.x + l.w + 0.004) * w))
                py0 = max(0, int((l_top - 0.003) * h))
                py1 = min(h, int((l_bot + 0.003) * h))
                arr[py0:py1, px0:px1] = 255

        left = max(0.0, dbox[0] - 0.022)
        right = min(1.0, dbox[2] + 0.022)
        if x_right_col < 1.0:
            right = min(right, x_right_col - 0.006)
        if x_left_col > 0.0:
            left = max(left, x_left_col + 0.006)
        top = max(0.0, dbox[1] - 0.022)
        bottom = min(1.0, dbox[3] + 0.022)

        x0, y0 = int(left * w), int(top * h)
        x1, y1 = int(right * w), int(bottom * h)
        if x1 <= x0 + 20:
            x0, x1 = int(max(0.0, dbox[0] - 0.01) * w), int(min(1.0, dbox[2] + 0.01) * w)
        sub = arr[y0:y1, x0:x1].copy()
        sh, sw = sub.shape[:2]

        try:
            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                Image.fromarray(sub).save(tmp.name)
                cop = eng.recognize_page(Path(tmp.name), 1)
                for cl in cop.lines:
                    ctxt = cl.text.strip()
                    ctop = 1.0 - (cl.y + cl.h)
                    cbot = 1.0 - cl.y
                    is_crop_cap = bool(cap_re.search(ctxt)) or (
                        ctop > 0.78 and any(ch.isdigit() for ch in ctxt) and len(ctxt) >= 4
                    )
                    is_crop_prose = len(ctxt.split()) >= 3 or len(ctxt) >= 10
                    if is_crop_cap or is_crop_prose:
                        cx0 = max(0, int((cl.x - 0.01) * sw))
                        cx1 = min(sw, int((cl.x + cl.w + 0.01) * sw))
                        cy0 = max(0, int((ctop - 0.01) * sh))
                        cy1 = min(sh, int((cbot + 0.01) * sh))
                        sub[cy0:cy1, cx0:cx1] = 255
        except (OSError, RuntimeError, ValueError):
            pass

        gray = np.mean(sub, axis=2)
        ink = gray < 215
        ch, cw = ink.shape
        border = max(4, int(min(ch, cw) * 0.01))
        ink[:border, :] = False
        ink[-border:, :] = False
        ink[:, :border] = False
        ink[:, -border:] = False

        ys, xs = np.where(ink)
        if len(ys) > 20:
            ymin = max(0, int(ys.min()) - pad_px)
            ymax = min(sh, int(ys.max()) + pad_px)
            xmin = max(0, int(xs.min()) - pad_px)
            xmax = min(sw, int(xs.max()) + pad_px)
            crop = Image.fromarray(sub[ymin:ymax, xmin:xmax])
        else:
            crop = Image.fromarray(sub)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        crop.save(out_path)
        return out_path

    @staticmethod
    def verify_cropped_diagram(image_path: Path) -> tuple[bool, list[str]]:
        import re

        from ..ocr.apple_vision import AppleVisionOCREngine

        issues: list[str] = []
        if not image_path.exists():
            return False, ["File does not exist"]
        with Image.open(image_path) as im:
            w, h = im.size
            arr = np.array(im.convert("L"))
        if w < 60 or h < 60:
            issues.append(f"Image too small ({w}x{h})")
        ink_ratio = float((arr < 215).mean())
        if ink_ratio < 0.003:
            issues.append(f"Image nearly blank (ink_ratio={ink_ratio:.4f})")
        if ink_ratio > 0.65:
            issues.append(f"Image overly dark (ink_ratio={ink_ratio:.4f})")

        cap_re = re.compile(TypeSafeJevVision.CAPTION_TOKEN_RE)
        try:
            eng = AppleVisionOCREngine(languages=["en-US"])
            op = eng.recognize_page(image_path, 1)
            for l in op.lines:
                t = l.text.strip()
                if cap_re.search(t):
                    issues.append(f"Leaked figure caption in crop: {t!r}")
                elif len(t.split()) >= 4 or len(t) >= 16:
                    issues.append(f"Leaked prose line in crop: {t!r}")
        except (OSError, RuntimeError, ValueError):
            pass

        return (len(issues) == 0), issues
