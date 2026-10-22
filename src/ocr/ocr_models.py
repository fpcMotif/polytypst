"""Self-hostable OCR models: what to install, how to prompt, and how to clean each one's output.

Standard library only, because the Colab worker uploads this file next to itself.
"""

import re
from dataclasses import dataclass, field

JINA_RUNTIME = "jina"
DEEPSEEK_INFER_RUNTIME = "deepseek-infer"
VLLM_CHAT_RUNTIME = "vllm-chat"

_GROUNDING = re.compile(
    r"<\|ref\|>.*?<\|/ref\|>\s*<\|det\|>.*?<\|/det\|>|<\|det\|>.*?<\|/det\|>", re.DOTALL
)
_FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_END_TOKENS = ("<｜end▁of▁sentence｜>", "<|im_end|>", "<|endoftext|>")

UNIVERSAL_TEX_PROMPT = (
    "Transcribe this document page into clean, high-fidelity Markdown resembling LaTeX source.\n"
    "Rules:\n"
    "1. Format all mathematical expressions, variables, and formulas in LaTeX syntax: use inline $...$ and display $$...$$.\n"
    "2. Preserve all mathematical symbols, operators, superscripts, subscripts, fractions, integrals, sums, and limits exactly.\n"
    "3. Format headings with Markdown (#, ##, ###) reflecting document structure.\n"
    "4. Bold structural environments (e.g. **Theorem 1.**, **Lemma 2.**, **Definition.**, **Proposition.**, **Proof.**, **Example.**).\n"
    "5. Label display equations with exact numbering if present (e.g. $$ f(x) = \\dots $$ (1)).\n"
    "6. Convert tables into clean Markdown or HTML tables.\n"
    "7. For diagrams and figures, transcribe any caption or figure title (e.g. FIG. 1, Figure 2, Fig. 1.1) as a standalone line and preserve natural reading order.\n"
    "8. Preserve all body text, notes, and references without omitting content."
)


@dataclass(frozen=True)
class OCRModel:
    key: str
    hf_id: str
    runtime: str
    params_b: float
    license: str
    pip: tuple[str, ...]
    fixed_prompt: str | None = None
    bytes_per_param: float = 2.0
    needs_bf16: bool = False
    min_compute_capability: float = 7.0
    max_tokens: int = 8192
    max_image_side: int | None = None
    infer_kwargs: dict[str, object] = field(default_factory=dict)

    @property
    def follows_book_prompt(self) -> bool:
        return self.fixed_prompt is None

    @property
    def batches_internally(self) -> bool:
        return self.runtime == VLLM_CHAT_RUNTIME

    def weights_gb(self) -> float:
        return self.params_b * self.bytes_per_param

    def vram_gb(self) -> float:
        """Weights plus room for activations and the KV cache of one 8k-token page."""
        return self.weights_gb() * 1.25 + 3.0

    def copies_per_gpu(self, vram_gb: float, requested: int) -> int:
        """vLLM batches inside one copy; other runtimes load copies until the VRAM is full."""
        if self.batches_internally:
            return 1
        return max(1, min(requested, int(vram_gb * 0.9 // self.vram_gb())))

    def prompt_for(self, book_prompt: str) -> str:
        return self.fixed_prompt if self.fixed_prompt is not None else book_prompt

    def clean(self, raw: str) -> str:
        text = raw
        for token in _END_TOKENS:
            text = text.replace(token, "")
        text = _GROUNDING.sub("", text)
        text = _FRONT_MATTER.sub("", text.lstrip())
        return re.sub(r"\n{3,}", "\n\n", text).strip()


_DEEPSEEK_EXTRAS = ("einops", "addict", "easydict", "pillow", "matplotlib", "psutil")

OCR_MODELS: dict[str, OCRModel] = {
    m.key: m
    for m in (
        OCRModel(
            key="jina-ocr-v1",
            hf_id="jinaai/jina-ocr-v1",
            runtime=JINA_RUNTIME,
            params_b=3.37,
            license="cc-by-nc-4.0",
            pip=("transformers", "accelerate", "einops", "timm", "pillow"),
            min_compute_capability=7.5,
            max_tokens=4096,
        ),
        OCRModel(
            key="unlimited-ocr",
            hf_id="baidu/Unlimited-OCR",
            runtime=DEEPSEEK_INFER_RUNTIME,
            params_b=3.34,
            license="mit",
            pip=("transformers==4.57.1", *_DEEPSEEK_EXTRAS),
            fixed_prompt="<image>document parsing.",
            needs_bf16=True,
            min_compute_capability=8.0,
            infer_kwargs={
                "base_size": 1024,
                "image_size": 640,
                "crop_mode": True,
                "max_length": 32768,
                "no_repeat_ngram_size": 35,
                "ngram_window": 128,
            },
        ),
        OCRModel(
            key="deepseek-ocr",
            hf_id="deepseek-ai/DeepSeek-OCR",
            runtime=DEEPSEEK_INFER_RUNTIME,
            params_b=3.34,
            license="mit",
            pip=("transformers==4.46.3", "tokenizers==0.20.3", *_DEEPSEEK_EXTRAS),
            fixed_prompt="<image>\n<|grounding|>Convert the document to markdown. ",
            needs_bf16=True,
            min_compute_capability=8.0,
            infer_kwargs={"base_size": 1024, "image_size": 640, "crop_mode": True},
        ),
        OCRModel(
            key="olmocr-2",
            hf_id="allenai/olmOCR-2-7B-1025-FP8",
            runtime=VLLM_CHAT_RUNTIME,
            params_b=8.29,
            license="apache-2.0",
            pip=("vllm",),
            fixed_prompt=(
                "Attached is one page of a document that you must process. "
                "Just return the plain text representation of this document as if you were reading it naturally. Convert equations to LateX and tables to HTML.\n"
                "If there are any figures or charts, label them with the following markdown syntax ![Alt text describing the contents of the figure](page_startx_starty_width_height.png)\n"
                "Return your output as markdown, with a front matter section on top specifying values for the primary_language, is_rotation_valid, rotation_correction, is_table, and is_diagram parameters."
            ),
            bytes_per_param=1.0,
            min_compute_capability=8.0,
            max_image_side=1288,
        ),
        OCRModel(
            key="qwen3-vl-8b",
            hf_id="Qwen/Qwen3-VL-8B-Instruct",
            runtime=VLLM_CHAT_RUNTIME,
            params_b=8.77,
            license="apache-2.0",
            pip=("vllm",),
            min_compute_capability=8.0,
            max_image_side=1600,
        ),
    )
}

DEFAULT_OCR_MODEL = "jina-ocr-v1"


def ocr_model(key: str) -> OCRModel:
    try:
        return OCR_MODELS[key]
    except KeyError:
        raise ValueError(
            f"Unknown OCR model {key!r}; expected one of {sorted(OCR_MODELS)}"
        ) from None
