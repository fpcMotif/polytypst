from typing import Any

import httpx

from .http_transcriber import EncodedImage, HttpRequest, HttpTranscriber

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiTranscriber(HttpTranscriber):
    def __init__(
        self,
        *,
        model: str,
        prompt: str,
        api_key: str,
        provenance: str,
        concurrency: int,
        max_side: int,
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            provenance=provenance,
            concurrency=concurrency,
            max_side=max_side,
            client=client,
        )
        self.url = GEMINI_ENDPOINT.format(model=model)
        self.prompt = prompt
        self.api_key = api_key

    def request(self, image: EncodedImage) -> HttpRequest:
        parts = [
            {"text": self.prompt},
            {"inline_data": {"mime_type": image.mime, "data": image.data}},
        ]
        return HttpRequest(
            self.url,
            {"contents": [{"parts": parts}], "generationConfig": {"temperature": 0}},
            {"x-goog-api-key": self.api_key},
        )

    def text(self, body: Any) -> str:
        return "".join(
            part.get("text", "") for part in body["candidates"][0]["content"]["parts"]
        )
