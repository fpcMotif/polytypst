"""macOS Neural Engine Vision OCR implementation using Vision.framework."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List

from .base import OCREngine, OCRLine, OCRPage

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


class AppleVisionOCREngine(OCREngine):
    def __init__(self, languages: List[str] | None = None):
        self.languages = languages or ["zh-Hans", "en-US", "ja-JP", "fr-FR"]
        self._compiled_binary = None

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

    def recognize_page(self, image_path: Path, page_number: int) -> OCRPage:
        pages = self.recognize_document([image_path])
        return pages[0] if pages else OCRPage(page_number, 0, 0, [])

    def recognize_document(self, image_paths: List[Path]) -> List[OCRPage]:
        bin_path = self._ensure_binary()
        with tempfile.TemporaryDirectory() as temp_in, tempfile.TemporaryDirectory() as temp_out:
            # Symlink or copy images
            for idx, p in enumerate(image_paths):
                target = Path(temp_in) / f"page_{idx+1:04d}{p.suffix}"
                os.symlink(p.resolve(), target)

            langs_arg = ",".join(self.languages)
            subprocess.run([str(bin_path), temp_in, temp_out, langs_arg], check=True)

            out_pages = []
            for idx, p in enumerate(image_paths):
                json_path = Path(temp_out) / f"page_{idx+1:04d}.json"
                if json_path.exists():
                    with open(json_path) as f:
                        data = json.load(f)
                    lines = [
                        OCRLine(
                            text=l["text"],
                            x=l["x"],
                            y=l["y"],
                            w=l["w"],
                            h=l["h"],
                            confidence=l.get("confidence", 1.0)
                        )
                        for l in data.get("lines", [])
                    ]
                    out_pages.append(OCRPage(idx + 1, data.get("width", 0), data.get("height", 0), lines))
                else:
                    out_pages.append(OCRPage(idx + 1, 0, 0, []))
            return out_pages
