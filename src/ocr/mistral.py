from typing import Any

import httpx

from .http_transcriber import EncodedImage, HttpRequest, HttpTranscriber

MISTRAL_OCR_ENDPOINT = "https://api.mistral.ai/v1/ocr"


class MistralTranscriber(HttpTranscriber):
    def __init__(
        self,
        *,
        model: str,
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
        self.model = model
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def request(self, image: EncodedImage) -> HttpRequest:
        body = {
            "model": self.model,
            "document": {"type": "image_url", "image_url": image.data_uri},
        }
        return HttpRequest(MISTRAL_OCR_ENDPOINT, body, self.headers)

    def text(self, body: Any) -> str:
        return str(body["pages"][0]["markdown"])
