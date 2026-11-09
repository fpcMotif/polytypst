from typing import Any

import httpx

from .http_transcriber import EncodedImage, HttpRequest, HttpTranscriber, PageFailed

INCOMPLETE_FINISH_REASONS = ("length", "content_filter")


class OpenAICompatTranscriber(HttpTranscriber):
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        prompt: str,
        api_key: str | None,
        provenance: str,
        concurrency: int,
        max_side: int,
        pace_sec: float = 0.0,
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            provenance=provenance,
            concurrency=concurrency,
            max_side=max_side,
            pace_sec=pace_sec,
            client=client,
        )
        self.url = f"{base_url.rstrip('/')}/chat/completions"
        self.model = model
        self.prompt = prompt
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def request(self, image: EncodedImage) -> HttpRequest:
        content = [
            {"type": "text", "text": self.prompt},
            {"type": "image_url", "image_url": {"url": image.data_uri}},
        ]
        body = {
            "model": self.model,
            "temperature": 0,
            "messages": [{"role": "user", "content": content}],
        }
        return HttpRequest(self.url, body, self.headers)

    def text(self, body: Any) -> str:
        choice = body["choices"][0]
        content = choice["message"]["content"]
        if not isinstance(content, str) or choice.get("finish_reason") in INCOMPLETE_FINISH_REASONS:
            raise PageFailed(f"no whole transcript: finish_reason {choice.get('finish_reason')!r}")
        return content
