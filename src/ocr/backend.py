import hashlib
import os
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import parse_qsl, urlencode

from .ocr_models import DEFAULT_OCR_MODEL, UNIVERSAL_TEX_PROMPT, ocr_model
from .pages import OCRBackendError

GEMINI_DEFAULT_MODEL = "gemini-3.1-pro-preview"

Option = int | str


@dataclass(frozen=True)
class BackendKind:
    default_model: str
    options: Mapping[str, Option]
    takes_prompt: bool = True
    self_hosted: bool = False


KINDS: Mapping[str, BackendKind] = MappingProxyType(
    {
        "gemini": BackendKind(
            GEMINI_DEFAULT_MODEL, {"concurrency": 4, "max_side": 2048}
        ),
        "openai": BackendKind(
            "",
            {
                "base_url": "https://api.openai.com/v1",
                "key_env": "OPENAI_API_KEY",
                "concurrency": 8,
                "max_side": 2048,
            },
        ),
        "jina": BackendKind(
            "jina-ocr-v1", {"concurrency": 1, "pace_ms": 1500, "max_side": 0}
        ),
        "mistral": BackendKind(
            "mistral-ocr-latest", {"concurrency": 2, "max_side": 0}, takes_prompt=False
        ),
        "local": BackendKind(DEFAULT_OCR_MODEL, {"shards": 1}, self_hosted=True),
        "colab": BackendKind(
            DEFAULT_OCR_MODEL,
            {"gpu": "G4", "workers": 2, "shards": 3, "batch": 70, "session": "ocr"},
            self_hosted=True,
        ),
        "cached": BackendKind("", {"dir": ""}, takes_prompt=False),
    }
)


def _option(kind: str, key: str, value: str) -> Option:
    if not isinstance(KINDS[kind].options[key], int):
        return value
    try:
        return int(value)
    except ValueError:
        raise ValueError(
            f"{kind} option {key} must be a whole number, got {value!r}"
        ) from None


@dataclass(frozen=True)
class Backend:
    kind: str
    model: str
    options: Mapping[str, Option]

    @classmethod
    def parse(cls, text: str) -> "Backend":
        head, _, query = text.partition("?")
        kind, _, model = head.partition(":")
        spec = KINDS.get(kind)
        if spec is None:
            raise ValueError(
                f"Unknown OCR backend {kind!r}; expected one of {', '.join(KINDS)}"
            )
        model = model or spec.default_model
        if spec.self_hosted:
            _ = ocr_model(model)
        elif kind != "cached" and not model:
            raise ValueError(f"{kind} needs a model, as in {kind}:MODEL")
        options = dict(spec.options)
        for key, value in parse_qsl(query, keep_blank_values=True):
            if key not in spec.options:
                raise ValueError(
                    f"{kind} has no option {key!r}; options: {', '.join(spec.options) or 'none'}"
                )
            options[key] = _option(kind, key, value)
        if kind == "cached" and not options["dir"]:
            raise ValueError("cached needs dir, as in cached:?dir=PATH")
        return cls(kind, model, MappingProxyType(options))

    def __str__(self) -> str:
        defaults = KINDS[self.kind].options
        changed = {k: v for k, v in self.options.items() if v != defaults[k]}
        query = f"?{urlencode(changed, safe='/:')}" if changed else ""
        return f"{self.kind}:{self.model}{query}"

    def number(self, key: str) -> int:
        return int(self.options[key])

    def text(self, key: str) -> str:
        return str(self.options[key])

    def prompt(self, book_prompt: str | None) -> str | None:
        wanted = book_prompt or UNIVERSAL_TEX_PROMPT
        if KINDS[self.kind].self_hosted:
            return ocr_model(self.model).prompt_for(wanted)
        return wanted if KINDS[self.kind].takes_prompt else None

    def provenance(self, prompt: str | None) -> str:
        made_by = f"{self.kind}:{self.model}"
        if prompt is None:
            return made_by
        return f"{made_by}#prompt={hashlib.sha256(prompt.encode()).hexdigest()[:12]}"


def api_key(env_name: str) -> str:
    key = os.environ.get(env_name, "")
    if not key:
        raise OCRBackendError(
            f"{env_name} is not set; `varlock load` shows what .env.schema provides"
        )
    return key
