from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from PIL import Image

from .figures_common import DARK_3B1B_THEME, MONO_THEME, Theme, fmt, validate_svg
from .figures_p1 import BUILDERS_P1
from .figures_p2 import BUILDERS_P2
from .figures_p3 import BUILDERS_P3
from .figures_p4 import BUILDERS_P4
from .figures_p5 import BUILDERS_P5
from .figures_p6 import BUILDERS_P6
from .figures_p7 import BUILDERS_P7
from .figures_p8 import BUILDERS_P8

ALL_BUILDERS: dict[str, Callable[[Theme], str]] = {
    **BUILDERS_P1,
    **BUILDERS_P2,
    **BUILDERS_P3,
    **BUILDERS_P4,
    **BUILDERS_P5,
    **BUILDERS_P6,
    **BUILDERS_P7,
    **BUILDERS_P8,
}

_DEFAULT_WF: dict[str, float] = {
    "fig_1": 0.5109,
    "fig_10": 0.9765,
    "fig_11": 0.6806,
    "fig_12": 0.6367,
    "fig_13": 0.7934,
    "fig_14": 0.6692,
    "fig_15": 0.6044,
    "fig_16": 0.6126,
    "fig_17": 0.9353,
    "fig_18": 0.3332,
    "fig_19": 0.3668,
    "fig_2": 0.8979,
    "fig_20": 0.3859,
    "fig_21": 0.7866,
    "fig_22": 0.735,
    "fig_23": 0.7834,
    "fig_24": 1.0,
    "fig_25": 0.9537,
    "fig_26": 0.9125,
    "fig_27": 0.9092,
    "fig_28": 0.5374,
    "fig_29": 0.4984,
    "fig_3": 0.6571,
    "fig_30": 0.6996,
    "fig_31": 0.4925,
    "fig_32": 0.492,
    "fig_33": 0.7025,
    "fig_34": 0.6632,
    "fig_35": 0.3484,
    "fig_36": 0.6886,
    "fig_37": 0.4861,
    "fig_38": 0.9387,
    "fig_39": 0.9038,
    "fig_4": 0.9952,
    "fig_40": 0.8899,
    "fig_41": 0.9048,
    "fig_42": 0.9387,
    "fig_43": 0.4711,
    "fig_44": 0.758,
    "fig_45": 1.0,
    "fig_46": 0.7181,
    "fig_47": 0.7421,
    "fig_48": 0.5922,
    "fig_49": 0.649,
    "fig_5": 0.7828,
    "fig_50": 0.5163,
    "fig_51": 0.7808,
    "fig_52": 0.5845,
    "fig_53": 0.3813,
    "fig_54": 0.7222,
    "fig_55": 0.4912,
    "fig_56": 1.0,
    "fig_57": 0.9355,
    "fig_58": 0.9355,
    "fig_59": 0.9353,
    "fig_6": 0.5913,
    "fig_60": 0.8917,
    "fig_61": 0.8746,
    "fig_62": 0.4418,
    "fig_63": 0.8538,
    "fig_64": 0.9575,
    "fig_65": 1.0,
    "fig_66": 0.4529,
    "fig_67": 0.7849,
    "fig_7": 0.9229,
    "fig_8": 0.5319,
    "fig_9": 0.9355,
    "fig_A-1": 0.9338,
    "fig_frontispiece": 0.7678,
    "fig_p028_inline": 0.8091,
    "fig_p031_inline": 0.7282,
    "fig_p032_inline": 0.7196,
    "fig_p041_inline": 0.7334,
    "fig_p042_inline": 0.7383,
    "fig_p047_inline": 0.3264,
    "fig_p048_inline_1": 0.7501,
    "fig_p048_inline_2": 0.7501,
    "fig_p059_inline_1": 0.7803,
    "fig_p059_inline_2": 0.481,
    "fig_p081_inline": 0.2112,
    "fig_p088_eq73": 0.6599,
    "fig_p088_inline": 0.6146,
    "fig_p102_inline_1": 0.2756,
    "fig_p102_inline_2": 0.2895,
    "fig_p111_inline_1": 0.7292,
    "fig_p111_inline_2": 0.4401,
    "fig_p117_inline": 0.9353,
    "fig_p126_inline_1": 0.2278,
    "fig_p126_inline_2": 0.7659,
    "fig_p129_inline": 0.7126,
    "fig_p178_inline_1": 0.7961,
    "fig_p178_inline_2": 0.7191,
    "fig_p180_inline_1": 0.3008,
    "fig_p180_inline_2": 0.7834,
    "fig_p184_inline": 0.7625,
    "fig_p187_block2x2": 0.05,
    "fig_p187_stencils37": 0.8179,
    "fig_p187_stencils4": 0.114,
    "fig_p192_inline": 0.3162,
    "fig_p199_inline": 0.4008,
    "fig_p211_inline": 0.5218,
    "fig_p217_inline_1": 0.72,
    "fig_p222_inline_1": 0.8443,
    "fig_p222_inline_2": 0.7522,
    "fig_p224_inline_1": 0.4404,
    "fig_p224_inline_2": 0.9279,
    "fig_p227_inline": 0.4265,
    "fig_p230_inline": 0.3938,
    "fig_p242_inline": 0.6286,
    "fig_p246_inline": 0.8184,
    "fig_p250_inline_1": 0.5354,
    "fig_p250_inline_2": 0.2191,
    "fig_p253_inline": 0.6836,
    "fig_p263_inline": 0.6762,
    "fig_p265_inline": 0.7753,
    "fig_p266_inline_1": 0.301,
    "fig_p266_inline_2": 0.2988,
    "fig_p269_inline_1": 0.11,
    "fig_p269_inline_2": 0.12,
    "fig_p269_inline_3": 0.11,
    "fig_p285_inline": 0.88,
    "fig_p314_inline_1": 0.8222,
    "fig_p314_inline_2": 0.1973,
    "fig_p328_inline": 0.6802,
    "fig_p371_paths": 0.1169,
    "fig_p374_inline_1": 0.6069,
    "fig_p374_inline_2": 0.5694,
    "fig_p378_inline": 0.3364,
    "fig_p390_inline": 0.5743,
    "fig_p395_inline": 0.6569,
    "fig_p403_inline": 0.7126,
    "fig_p404_inline_1": 0.8904,
    "fig_p404_inline_2": 0.7384,
    "fig_p404_inline_3": 0.6626,
    "fig_p404_inline_4": 0.5104,
    "fig_p422_inline": 0.8891,
    "fig_p446_inline": 0.8404,
    "fig_p447_inline": 0.9047,
    "fig_p454_inline_1": 0.7806,
    "fig_p454_inline_2": 0.6359,
    "fig_p455_inline_1": 0.5115,
    "fig_p455_inline_2": 0.6095,
    "fig_p455_inline_3": 0.6297,
    "fig_p456_table1": 0.8992,
    "fig_p459_table2": 0.8992,
    "fig_p461_inline_1": 0.5946,
    "fig_p461_inline_2": 0.7343,
    "fig_p461_inline_3": 0.5775,
    "fig_p461_inline_4": 0.8573,
    "fig_p463_table3": 0.8992,
    "fig_p465_inline": 0.7245,
    "fig_p466_inline_1": 0.385,
    "fig_p466_inline_2": 0.3879,
    "fig_p470_inline_1": 0.3782,
    "fig_p470_inline_2": 0.8008,
    "fig_p472_table4": 0.8112,
    "fig_p477_inline_1": 0.2846,
    "fig_p477_inline_2": 0.2282,
    "fig_p477_inline_3": 0.2846,
    "fig_p480_inline_1": 0.3782,
    "fig_p480_inline_2": 0.7244,
    "fig_p483_inline": 0.5115,
    "fig_p485_inline_1": 0.81,
    "fig_p485_inline_2": 0.81,
    "fig_p485_inline_3": 0.81,
    "fig_p486_inline": 0.8208,
    "fig_p493_inline": 0.8393,
    "fig_p500_inline": 0.7783,
    "fig_p504_inline_1": 0.6665,
    "fig_p505_inline_1": 0.9428,
    "fig_p505_inline_2": 0.7564,
    "fig_p507_inline": 0.7893,
    "fig_p508_inline": 0.6972,
    "fig_p517_inline": 0.7586,
    "fig_p518_inline": 0.7499,
    "fig_p519_inline": 0.7235,
    "fig_p523_inline": 0.5613,
    "fig_p527_inline": 0.6753,
    "fig_p527_inline_2": 0.05,
    "fig_p529_inline": 0.876,
    "fig_p539_inline": 0.27,
    "fig_p547_inline": 0.8636,
    "fig_p561_inline": 0.2894,
    "fig_p564_inline_1": 0.2756,
    "fig_p564_inline_2": 0.8579,
    "fig_p565_inline_1": 0.1717,
    "fig_p565_inline_2": 0.198,
    "fig_p578_inline_1": 0.7542,
    "fig_p578_inline_2": 0.3657,
    "fig_p580_inline_1": 0.5052,
    "fig_p580_inline_2": 0.2034,
    "fig_p586_inline_1": 0.78,
    "fig_p586_inline_2": 0.78,
    "fig_p635_inline_1": 0.8498,
    "fig_p635_inline_2": 0.4295,
    "fig_p636_inline_1": 0.2559,
    "fig_p636_inline_2": 0.8582,
    "fig_p636_inline_3": 0.7555,
    "fig_p637_inline": 0.635,
    "fig_p640_inline_1": 0.397,
    "fig_p640_inline_2": 0.8246,
    "fig_p641_inline": 0.7319,
    "fig_p650_inline_1": 0.9171,
    "fig_p650_inline_2": 0.7485,
    "fig_p653_inline": 0.5398,
    "fig_p657_inline": 0.8694,
    "fig_p669_inline": 0.1798,
    "fig_p669_pistol": 0.057,
    "fig_p671_inline": 0.4262,
    "fig_p672_inline": 0.8748,
    "fig_p682_inline_1": 0.7954,
    "fig_p682_inline_2": 0.4311,
    "fig_p684_inline": 0.9003,
    "fig_p685_inline_1": 0.3241,
    "fig_p685_inline_2": 0.324,
    "fig_p686_inline": 0.2713,
    "fig_p691_inline": 0.866,
    "fig_p738_inline": 0.0855,
    "fig_p759_inline": 0.225,
    "fig_p762_inline": 0.4121,
    "fig_p763_inline": 0.1535,
    "fig_p777_inline": 0.8406,
    "fig_p781_inline": 0.2844,
    "fig_p794_inline_1": 0.4311,
    "fig_p794_inline_2": 0.7389,
    "fig_p795_inline": 0.2955,
    "fig_p796_inline_1": 0.5558,
    "fig_p796_inline_2": 0.6897,
    "fig_p797_inline": 0.8781,
    "fig_p800_inline": 0.6897,
    "fig_p812_inline_1": 0.8358,
    "fig_p812_inline_2": 0.8537,
    "fig_p817_inline": 0.2829,
    "fig_p823_inline": 0.1969,
    "fig_p825_inline_1": 0.1305,
    "fig_p825_inline_2": 0.1315,
    "fig_p825_inline_3": 0.1316,
    "fig_p825_inline_4": 0.1644,
    "fig_p826_inline_1": 0.0614,
    "fig_p826_inline_2": 0.0592,
    "fig_p827_inline": 0.1601,
    "fig_p829_inline_1": 0.7917,
    "fig_p829_inline_2": 0.7917,
    "fig_p830_inline": 0.7917,
}

_NUMBERED_RE = re.compile(r"^fig_\d+[a-z]?$")
_HEAD_RE = re.compile(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)" width="[0-9.]+" height="[0-9.]+"')


def _load_wf_map(out_dir: Path) -> dict[str, float]:
    wf = dict(_DEFAULT_WF)
    manifest = out_dir / "figures_manifest.json"
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        items = data.get("figures", data) if isinstance(data, dict) else data
        for entry in items:
            fid = str(entry.get("figure_id", ""))
            box = entry.get("box")
            if fid and isinstance(box, list) and len(box) == 4:
                stem = fid if fid.startswith("fig_") else f"fig_{fid}"
                span = round(max(0.05, min(1.0, float(box[2]) - float(box[0]))), 4)
                wf[stem] = span
                if stem == "fig_A_1":
                    wf["fig_A-1"] = span
    return wf


def _frame_svg_for_typst(svg_text: str, stem: str, wf: float, theme: Theme) -> str:
    if _NUMBERED_RE.match(stem):
        return svg_text
    m = _HEAD_RE.search(svg_text)
    if not m:
        return svg_text
    vw = float(m.group(1))
    vh = float(m.group(2))
    target_frac = min(0.75, max(0.10, wf / 0.78))
    if target_frac >= 0.749:
        return svg_text
    target_vw = round(vw * 0.75 / target_frac, 2)
    if target_vw <= vw + 0.5:
        return svg_text
    pad = round((target_vw - vw) / 2.0, 2)
    new_head = f'viewBox="{fmt(-pad)} 0 {fmt(target_vw)} {fmt(vh)}" width="{fmt(target_vw)}" height="{fmt(vh)}"'
    framed = svg_text.replace(m.group(0), new_head, 1)
    if not theme.is_dark:
        old_bg = f'<rect x="0" y="0" width="{fmt(vw)}" height="{fmt(vh)}" rx="0" fill="{theme.bg}"/>'
        new_bg = f'<rect x="{fmt(-pad)}" y="0" width="{fmt(target_vw)}" height="{fmt(vh)}" rx="0" fill="{theme.bg}"/>'
        framed = framed.replace(old_bg, new_bg, 1)
    return framed


def _stamp_png_300dpi(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im.save(dst, format="PNG", dpi=(300, 300))


def _batch_render_pngs(jobs: list[tuple[str, str, float, Path]]) -> None:
    if not jobs:
        return
    typst_bin = shutil.which("typst")
    if typst_bin is None:
        raise RuntimeError("typst binary not found on PATH")
    with tempfile.TemporaryDirectory(prefix="knuth4a_figs_") as tmp_s:
        tmp = Path(tmp_s)
        pages: list[str] = []
        for idx, (_, raw_svg, wf, _) in enumerate(jobs):
            svg_name = f"s_{idx:04d}.svg"
            (tmp / svg_name).write_text(raw_svg, encoding="utf-8")
            phys_w = round(min(0.92, max(0.12, wf / 0.78)) * 345.0, 2)
            pages.append(
                f'#page(width: {phys_w}pt, height: auto, margin: 0pt)[#image("{svg_name}", width: 100%)]'
            )
        sheet_typ = tmp / "sheet.typ"
        sheet_typ.write_text("\n".join(pages) + "\n", encoding="utf-8")
        out_tpl = tmp / "p_{0p}.png"
        subprocess.run(
            [typst_bin, "compile", "--format", "png", "--ppi", "300", str(sheet_typ), str(out_tpl)],
            check=True,
            capture_output=True,
            text=True,
        )
        rendered = sorted(tmp.glob("p_*.png"))
        if len(rendered) != len(jobs):
            raise RuntimeError(f"Expected {len(jobs)} PNGs from typst, got {len(rendered)}")
        for src_png, (_, _, _, dst_png) in zip(rendered, jobs, strict=True):
            _stamp_png_300dpi(src_png, dst_png)


def build_all_figures(out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir)
    mono_dir = out_dir / "figures"
    dark_dir = out_dir / "figures_color"
    mono_dir.mkdir(parents=True, exist_ok=True)
    dark_dir.mkdir(parents=True, exist_ok=True)
    wf_map = _load_wf_map(out_dir)
    written: list[Path] = []
    png_jobs: list[tuple[str, str, float, Path]] = []

    for key in sorted(ALL_BUILDERS):
        builder = ALL_BUILDERS[key]
        stem = key if key.startswith("fig_") else f"fig_{key}"
        wf = wf_map.get(stem, 0.55)
        raw_mono = builder(MONO_THEME)
        raw_dark = builder(DARK_3B1B_THEME)
        validate_svg(raw_mono)
        validate_svg(raw_dark)
        framed_mono = _frame_svg_for_typst(raw_mono, stem, wf, MONO_THEME)
        framed_dark = _frame_svg_for_typst(raw_dark, stem, wf, DARK_3B1B_THEME)
        validate_svg(framed_mono)
        validate_svg(framed_dark)

        mono_svg_path = mono_dir / f"{stem}.svg"
        dark_svg_path = dark_dir / f"{stem}.svg"
        mono_png_path = mono_dir / f"{stem}.png"
        dark_png_path = dark_dir / f"{stem}.png"

        mono_svg_path.write_text(framed_mono, encoding="utf-8")
        dark_svg_path.write_text(framed_dark, encoding="utf-8")
        written.extend([mono_svg_path, dark_svg_path, mono_png_path, dark_png_path])
        png_jobs.append((stem, raw_mono, wf, mono_png_path))
        png_jobs.append((stem, raw_dark, wf, dark_png_path))

    _batch_render_pngs(png_jobs)

    for folder in (mono_dir, dark_dir):
        for ext in ("svg", "png"):
            src_a = folder / f"fig_A-1.{ext}"
            dst_a = folder / f"fig_A_1.{ext}"
            if src_a.is_file():
                shutil.copy2(src_a, dst_a)
                written.append(dst_a)

    return written
