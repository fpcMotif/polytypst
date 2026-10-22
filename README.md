# polytypst: Universal Document Intelligence & Beautiful Typesetting Compiler

`polytypst` transforms complex, scanned, or born-digital academic and technical PDFs into publication-grade **Typst**, **LaTeX**, and reflowable **EPUB** documents, with automated figure extraction, vision-grounded placement, and multilingual typography.

---

## 🌟 Highlights

- **Universal Multilingual Support**: Built-in support for CJK (Simplified & Traditional Chinese, Japanese, Korean) and Western languages (English, French, German, Spanish, Latin).
- **Vision-Grounded Figure Placement**:
  - Detects diagrams, flowcharts, and technical plots.
  - Integrates **TypeSafe Jev 1.14** (`jev-preview` / `jev-1.14.0`) System One multimodal model with `Box` and `Noul` primitives (`TypeSafe-Danger-Zone-Images: true`) for zero-shot diagram localization.
  - Extracts 300 DPI high-resolution figures with automatic dust, skew, and margin cleanup.
  - Positions figures semantically within the exact text paragraph where they are referenced and discussed.
- **Multi-Engine OCR Stack**:
  - **macOS Neural Engine Vision**: Fast, offline, Apple Silicon-accelerated (`VNRecognizeTextRequest`). Processes a 192-page book in **79 seconds** with zero CJK spacing corruption.
  - **Mistral Document OCR (`mistral-ocr-latest`)**: High-accuracy cloud OCR with LaTeX math and Markdown table preservation.
  - **Tesseract 5.5**: Cross-platform offline OCR fallback supporting 129 languages.
  - **Native PyMuPDF / PDFium**: Direct vector extraction for born-digital PDFs.
- **Multi-Target Compilers**:
  - **Typst (`.typ` & `.pdf`)**: Modern, blazing-fast (<2s) book compilation with font cascades (`PingFang SC`, `Songti SC`, `Hiragino Sans GB`, `Libertinus Serif`, `STIX Two Math`), alternating running headers, margin folios, drop caps, and interactive TOC bookmarks.
  - **EPUB (`.epub`)**: Reflowable e-book format for Apple Books, Kindle, and Kobo, bundled with embedded high-resolution graphics and tailored CSS typography.
  - **LaTeX (`.tex`)**: Clean `ctexbook`XeLaTeX source with microtype and professional table styling.

---

## 🏗️ Architecture

```
                       Input PDF (Scanned or Vector)
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
     Page-by-Page Rendering                    TOC & Metadata Engine
       (MuPDF / PDFium)                         (Frontmatter, CIP, CIP)
               │                                         │
               ▼                                         │
     Multi-Engine OCR Stack                              │
  ┌──────────────────────────┐                           │
  │ • Apple Silicon Vision   │                           │
  │ • Mistral Document OCR   │                           │
  │ • Tesseract 5 (129 langs)│                           │
  └────────────┬─────────────┘                           │
               ▼                                         │
     Vision Grounding & Cropping                         │
  ┌──────────────────────────┐                           │
  │ • TypeSafe Jev 1.14 Box  │                           │
  │ • Content-Aware Trimmer  │                           │
  │ • Semantic Grounder      │                           │
  └────────────┬─────────────┘                           │
               ▼                                         │
       Document Stitcher ◄───────────────────────────────┘
  (Header/Footer Strip, Paragraph Join, Heading Tree)
               │
               ├──────────────────────┬──────────────────────┐
               ▼                      ▼                      ▼
        Typst Compiler         Pandoc EPUB            LaTeX Compiler
     (PingFang / Songti)   (Reflowable CSS)        (CTeX / Booktabs)
               │                      │                      │
               ▼                      ▼                      ▼
           book.pdf               book.epub              book.tex
```

---

## 🚀 Quick Start

### Installation

```bash
cd polytypst
uv pip install -e .
```

### CLI Usage

```bash
# Transcribe a scanned PDF with the Gemini API, then compile it
polytypst path/to/document.pdf --output output/book --backend gemini

# A folder of page photos, or a single image, works the same way
polytypst path/to/photos/ --output output/book --backend gemini
```

### Options

| Flag | Description | Default |
|---|---|---|
| `--book` | Key of the book in `src/KEY/` that the scan is | the book the file name matches, else a new book |
| `-o, --output` | Output folder of a new book; a known book writes to `output/KEY/` | `output/<slug>/` |
| `--backend` | OCR backend as `KIND[:MODEL][?KEY=VALUE&...]`: `gemini`, `openai`, `jina`, `mistral`, `local`, `colab` or `cached` | `colab` |
| `--pages` | Transcribe only these pages, as in `3,7-9` | every page |
| `--retranscribe` | Redo transcripts that another backend or prompt made | off |
| `--publisher`, `--lang`, `--domain` | Composition presets of a new book; a known book refuses them | `cambridge`, `en`, `math` |

`docs/scanned-books.md` describes each backend, its API key, and how the transcript store resumes a run.

---

## 📚 Benchmark Showcase: John Roberts' *The Modern Firm*

Tested on the complete 192-page scanned academic translation:
**《现代企业：基于绩效与增长的组织设计》** (*The Modern Firm: Organizational Design for Performance and Growth*), John Roberts (Stanford GSB), Contemporary World Academic Masterpieces series.

- **Source**: 192 scanned pages (DuXiu scan from Anna's Archive, zero embedded text).
- **OCR Speed**: All 192 pages recognized in **79.11s** via parallel Apple Silicon Neural Engine.
- **Figures Grounded**: All **9 core economic diagrams** detected, cropped at 300 DPI, and semantically placed:
  1. *Fig 1: Design problem: Strategy, Organization, and Environment -> Performance* (p. 28)
  2. *Fig 2: Complementarities and Discrete Matching: Ford vs. Toyota* (p. 42)
  3. *Fig 3: Classical Concave Choice and Performance Relationship* (p. 52)
  4. *Fig 4: Shifted Choice and Performance Curve* (p. 54)
  5. *Fig 5: Non-Concave Performance Landscape (Multiple Peaks)* (p. 56)
  6. *Fig 6: Contour Map of Non-Concave Landscape with Peaks A and B* (p. 57)
  7. *Fig 7: Discontinuous Jump in Optimal Performance over Time* (p. 60)
  8. *Fig 8: Feasible Frontier of Cooperation and Initiative* (p. 92)
  9. *Fig 9: Long-Term Relationships Expanding Behavioral Combinations* (p. 154)
- **Typst Output**: 232-page publication-grade PDF compiled in **1.17s** with PingFang SC & Songti typography.
- **EPUB Output**: 490 KB responsive reflowable e-book with 9 embedded images and complete 12-chapter table of contents.
- **LaTeX Output**: 440 KB clean XeLaTeX/CTeX source.
