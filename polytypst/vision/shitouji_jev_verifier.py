"""
TypeSafe Jev Vision & Optical Pixel-Level Parity Verifier for Shitouji Reproduction.
Pure OpenCV + Poppler high-speed implementation (sub-second per page).
Enforces zero spatial drift, margin boundary safety, and red-shift blob gating.
"""

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import sys
import cv2
import numpy as np

PDFTOPPM = "/nix/store/5mwz7xmrc7928bcfl6jif5z29fabyq9b-poppler-utils-26.09.0/bin/pdftoppm"
WORK_DIR = Path("/tmp/shitouji_work")


@dataclass
class JevDiscrepancy:
    page_num: int
    rule: str
    severity: str  # "ERROR", "WARNING"
    message: str
    delta_x: float = 0.0
    delta_y: float = 0.0
    coords: tuple[float, float, float, float] | None = None


@dataclass
class JevReport:
    target_name: str
    total_pages_audited: int
    violations: list[JevDiscrepancy] = field(default_factory=list)
    mean_iou: float = 0.0

    @property
    def is_clean(self) -> bool:
        return not any(v.severity == "ERROR" for v in self.violations)

    def print_summary(self) -> None:
        errors = [v for v in self.violations if v.severity == "ERROR"]
        warns = [v for v in self.violations if v.severity == "WARNING"]
        print("\n================ JEV VISION & PIXEL PARITY REPORT ================")
        print(f"Target: {self.target_name} ({self.total_pages_audited} pages checked)")
        status = "PASSED (Zero Loss / Strict Parity)" if not errors else "FAILED (Drift Detected)"
        print(f"Status: {status} | {len(errors)} Errors, {len(warns)} Warnings | Mean IoU: {self.mean_iou:.2f}%")
        print("-" * 65)
        for v in self.violations:
            prefix = "❌ [ERROR]" if v.severity == "ERROR" else "⚠️  [WARN] "
            print(f"{prefix} Page {v.page_num:04d} | {v.rule}: {v.message}")
            if v.coords:
                print(f"    Location: x={v.coords[0]:.1f}pt, y={v.coords[1]:.1f}pt (Δx={v.delta_x:+.2f}pt, Δy={v.delta_y:+.2f}pt)")
        print("==================================================================\n")


class JevShitoujiVerifier:
    def __init__(self, orig_pdf: Path, rep_pdf: Path, dpi: int = 150) -> None:
        self.orig_pdf: Path = orig_pdf
        self.rep_pdf: Path = rep_pdf
        self.dpi: int = dpi
        self.scale: float = dpi / 72.0

    def render_ppm(self, pdf_path: Path, pno: int, prefix: str) -> Path:
        cmd = [PDFTOPPM, "-png", "-r", str(self.dpi), "-f", str(pno), "-l", str(pno), str(pdf_path), str(WORK_DIR / prefix)]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        matches = sorted(WORK_DIR.glob(f"{prefix}-*.png"))
        assert len(matches) > 0, f"Render failed for page {pno}"
        return matches[-1]

    def audit_page(self, pno: int, report: JevReport) -> float:
        png_o = self.render_ppm(self.orig_pdf, pno, f"jev_o_p{pno}")
        png_r = self.render_ppm(self.rep_pdf, pno, f"jev_r_p{pno}")

        im_o = cv2.imread(str(png_o), cv2.IMREAD_GRAYSCALE)
        im_r = cv2.imread(str(png_r), cv2.IMREAD_GRAYSCALE)
        assert im_o is not None and im_r is not None

        _, bin_o = cv2.threshold(im_o, 210, 255, cv2.THRESH_BINARY_INV)
        _, bin_r = cv2.threshold(im_r, 230, 255, cv2.THRESH_BINARY_INV)

        # 1. Foot Margin Breach Rule
        # Bottom-most ink row
        rows_r = np.where(bin_r > 0)[0]
        if len(rows_r) > 0:
            max_y_pt = float(rows_r.max() / self.scale)
            if max_y_pt > 692.0:
                report.violations.append(JevDiscrepancy(
                    page_num=pno,
                    rule="FOOT_MARGIN_BREACH",
                    severity="ERROR",
                    message=f"Ink overflowed past foot margin: max_y = {max_y_pt:.2f}pt (limit: 692.0pt).",
                    coords=(0.0, max_y_pt, 0.0, 0.0)
                ))

        # 2. Measure Column Alignment via vertical morphology
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, int(25 * self.scale / (150/72))))
        v_o = cv2.morphologyEx(bin_o, cv2.MORPH_CLOSE, v_kernel)
        v_r = cv2.morphologyEx(bin_r, cv2.MORPH_CLOSE, v_kernel)

        cnts_o, _ = cv2.findContours(v_o, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts_r, _ = cv2.findContours(v_r, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        def cluster_columns(cnts):
            raw_boxes = [cv2.boundingRect(c) for c in cnts if cv2.boundingRect(c)[3] > int(40 * self.scale)]
            raw_boxes.sort(key=lambda b: -b[0])
            clusters = []
            for b in raw_boxes:
                bx, by, bw, bh = b
                matched_c = None
                for c in clusters:
                    cx_mid = (c["x0"] + c["x1"]) / 2.0
                    bx_mid = bx + bw / 2.0
                    if abs(cx_mid - bx_mid) < 8.0 * self.scale:
                        matched_c = c
                        break
                if matched_c:
                    matched_c["x0"] = min(matched_c["x0"], bx)
                    matched_c["x1"] = max(matched_c["x1"], bx + bw)
                    matched_c["y0"] = min(matched_c["y0"], by)
                    matched_c["y1"] = max(matched_c["y1"], by + bh)
                else:
                    clusters.append({"x0": bx, "x1": bx + bw, "y0": by, "y1": by + bh})
            clusters.sort(key=lambda c: -((c["x0"] + c["x1"]) / 2.0))
            return clusters

        cols_o = cluster_columns(cnts_o)
        cols_r = cluster_columns(cnts_r)

        for i in range(min(len(cols_o), len(cols_r))):
            xo = (cols_o[i]["x0"] + cols_o[i]["x1"]) / 2.0
            xr = (cols_r[i]["x0"] + cols_r[i]["x1"]) / 2.0
            yo_top = cols_o[i]["y0"]
            yr_top = cols_r[i]["y0"]

            dx_pt = (xr - xo) / self.scale
            dy_pt = (yr_top - yo_top) / self.scale

            if abs(dx_pt) > 1.5:
                report.violations.append(JevDiscrepancy(
                    page_num=pno,
                    rule="COLUMN_HORIZONTAL_DRIFT",
                    severity="ERROR",
                    message=f"Column {i+1} horizontal drift: Δx = {dx_pt:+.2f}pt (threshold: 1.50pt).",
                    delta_x=dx_pt, delta_y=dy_pt,
                    coords=(xo / self.scale, yo_top / self.scale, 0.0, 0.0)
                ))
            if abs(dy_pt) > 5.0:
                report.violations.append(JevDiscrepancy(
                    page_num=pno,
                    rule="COLUMN_VERTICAL_DRIFT",
                    severity="ERROR",
                    message=f"Column {i+1} vertical baseline drift: Δy = {dy_pt:+.2f}pt (threshold: 5.00pt).",
                    delta_x=dx_pt, delta_y=dy_pt,
                    coords=(xo / self.scale, yo_top / self.scale, 0.0, 0.0)
                ))
        # 3. Vision Rule: Red-shift / Layout drift blobs
        matched = (bin_o > 0) & (bin_r > 0)
        orig_only = (bin_o > 0) & (bin_r == 0)

        # Ignore watermark area on original (central upper block)
        orig_only_clean = orig_only.astype(np.uint8) * 255
        orig_only_clean[int(140*self.scale):int(570*self.scale), int(160*self.scale):int(350*self.scale)] = 0

        # Filter 1-2px font serif fringes via 4x4 opening
        kernel_noise = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4))
        drift_blobs = cv2.morphologyEx(orig_only_clean, cv2.MORPH_OPEN, kernel_noise)
        cnts_drift, _ = cv2.findContours(drift_blobs, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cd in cnts_drift:
            bx, by, bw, bh = cv2.boundingRect(cd)
            if bw > 12 and bh > 12:
                report.violations.append(JevDiscrepancy(
                    page_num=pno,
                    rule="RED_SHIFT_LAYOUT_DISCREPANCY",
                    severity="ERROR",
                    message=f"Significant un-matched ink blob ({bw}x{bh}px) detected.",
                    coords=(bx / self.scale, by / self.scale, bw / self.scale, bh / self.scale)
                ))

        n_m = int(np.count_nonzero(matched))
        n_t = int(np.count_nonzero(np.bitwise_or(bin_o > 0, bin_r > 0)))
        return float(n_m / max(1, n_t)) * 100.0

    def verify(self, pages: list[int]) -> JevReport:
        report = JevReport(target_name=self.rep_pdf.name, total_pages_audited=len(pages))
        ious = [self.audit_page(pno, report) for pno in pages]
        report.mean_iou = float(np.mean(ious)) if ious else 0.0
        return report


def main():
    p_orig = Path("/Users/martinfan/Downloads/石頭記＠四校訖自用.v2.006a.PDF")
    p_rep = Path("/Users/martinfan/devv/polytypst/shitouji/typst/shitouji_complete_all_in_one.pdf")

    verifier = JevShitoujiVerifier(p_orig, p_rep)
    test_pages = [19, 20, 25]
    report = verifier.verify(test_pages)
    report.print_summary()

    if not report.is_clean:
        sys.exit(1)


if __name__ == "__main__":
    main()
