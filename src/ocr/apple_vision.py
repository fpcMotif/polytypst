"""macOS Neural Engine Vision OCR implementation using Vision.framework."""

import json
import os
import subprocess
import tempfile
from collections.abc import Iterator, Sequence
from pathlib import Path

from .pages import LinePage, OcrLine, PageImage

SWIFT_HARNESS_CODE = """
import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
if args.count < 3 { exit(1) }

let inDir = args[1]
let outDir = args[2]
let langs = args.count > 3 ? args[3].components(separatedBy: ",") : ["zh-Hans", "en-US"]

let fm = FileManager.default
let files = try fm.contentsOfDirectory(atPath: inDir).filter { $0.hasSuffix(".png") || $0.hasSuffix(".jpg") }.sorted()

DispatchQueue.concurrentPerform(iterations: files.count) { idx in
    let filename = files[idx]
    let inPath = (inDir as NSString).appendingPathComponent(filename)
    let baseName = (filename as NSString).deletingPathExtension
    let outPath = (outDir as NSString).appendingPathComponent(baseName + ".json")
    
    if fm.fileExists(atPath: outPath) { return }
    
    guard let img = NSImage(contentsOfFile: inPath),
          let cgImage = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { return }
          
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = langs
    request.usesLanguageCorrection = true
    
    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try? handler.perform([request])
    
    var lines: [[String: Any]] = []
    if let results = request.results {
        let sorted = results.sorted(by: { $0.boundingBox.origin.y > $1.boundingBox.origin.y })
        for obs in sorted {
            let b = obs.boundingBox
            lines.append([
                "text": obs.topCandidates(1).first?.string ?? "",
                "x": b.origin.x,
                "y": b.origin.y,
                "w": b.size.width,
                "h": b.size.height,
                "confidence": obs.confidence
            ])
        }
    }
    
    let pageNum = Int(baseName.components(separatedBy: "_").last ?? "0") ?? (idx + 1)
    let payload: [String: Any] = [
        "page": pageNum,
        "width": cgImage.width,
        "height": cgImage.height,
        "lines": lines
    ]
    if let data = try? JSONSerialization.data(withJSONObject: payload, options: []) {
        try? data.write(to: URL(fileURLWithPath: outPath))
    }
}
"""


class AppleVisionReader:
    def __init__(self, languages: Sequence[str]):
        self.languages = tuple(languages)
        self._compiled_binary = None

    @property
    def provenance(self) -> str:
        return "apple-vision:" + ",".join(self.languages)

    def _ensure_binary(self) -> Path:
        if self._compiled_binary and self._compiled_binary.exists():
            return self._compiled_binary

        cache_dir = Path.home() / ".cache" / "polytypst"
        cache_dir.mkdir(parents=True, exist_ok=True)
        bin_path = cache_dir / "apple_vision_runner"

        if not bin_path.exists():
            with tempfile.NamedTemporaryFile("w", suffix=".swift", delete=False) as f:
                f.write(SWIFT_HARNESS_CODE)
                swift_src = f.name
            subprocess.run(["swiftc", "-O", swift_src, "-o", str(bin_path)], check=True)
            os.remove(swift_src)

        self._compiled_binary = bin_path
        return bin_path

    def read(self, pages: Sequence[PageImage]) -> Iterator[LinePage]:
        bin_path = self._ensure_binary()
        with tempfile.TemporaryDirectory() as temp_in, tempfile.TemporaryDirectory() as temp_out:
            # Symlink or copy images
            for idx, page in enumerate(pages):
                target = Path(temp_in) / f"page_{idx + 1:04d}{page.path.suffix}"
                os.symlink(page.path.resolve(), target)

            langs_arg = ",".join(self.languages)
            subprocess.run([str(bin_path), temp_in, temp_out, langs_arg], check=True)

            for idx, page in enumerate(pages):
                json_path = Path(temp_out) / f"page_{idx + 1:04d}.json"
                if not json_path.exists():
                    continue
                data = json.loads(json_path.read_text(encoding="utf-8"))
                lines = tuple(
                    OcrLine(line["text"], line["x"], line["y"], line["w"], line["h"], line.get("confidence", 1.0))
                    for line in data.get("lines", [])
                )
                yield LinePage(page.number, lines)
