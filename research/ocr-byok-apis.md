# Jina and Mistral OCR APIs for a bring-your-own-key flow

Ticket: devv-o5is. Research date: 2026-10-17.

## Answer

Mistral OCR 4.1 fits a bring-your-own-key (BYOK) flow better than Jina. A BYOK flow is one where our backend stores the user's own provider key and calls the provider with it. Mistral has one documented endpoint, a fixed price of $4 per 1,000 pages, whole-PDF input up to 50 MB and 1,000 pages, and a page-range parameter. Its terms also allow commercial use. Jina's `jina-ocr-v1` reports a strong formula score (OmniDocBench formula CDM 93.28). However, its weights are CC BY-NC 4.0, its price per page is not published, and the hosted endpoint can return HTTP 503 on a cold start. For math fidelity, neither vendor publishes a LaTeX guarantee for the current model. We must run both on our own pages before we commit. Recommendation: make Mistral OCR 4.1 the default BYOK engine, keep Jina as an optional second engine, and run a math-page bake-off.

## Mistral OCR

**Current model.** OCR 4.1 has the API id `mistral-ocr-4-1`. It was released on 2026-07-16 and became generally available on 2026-08-31. The aliases `mistral-ocr-latest` and `mistral-ocr-4` point to it. OCR 4.0 (`mistral-ocr-4-0`) was deprecated on 2026-09-29 and retired on 2026-09-30. OCR 3 (`mistral-ocr-2512`) is still available. ([changelog](https://docs.mistral.ai/resources/changelogs), [models overview](https://docs.mistral.ai/getting-started/models/models_overview/)) The user's "v4" is therefore OCR 4.1 today. The model page shows the id as "mistral-ocr-4-1+2". The changelog uses `mistral-ocr-4-1`. Unverified: which exact string the API accepts besides the aliases. ([OCR 4.1 model page](https://docs.mistral.ai/models/ocr-4-1))

**Endpoint and auth.** The endpoint is `POST https://api.mistral.ai/v1/ocr` with `Authorization: Bearer $MISTRAL_API_KEY` and a JSON body. ([API reference](https://docs.mistral.ai/api/endpoint/ocr))

**Input formats.** The `document` field takes a `document_url` chunk, an `image_url` chunk, or an uploaded file. A PDF can be a public URL, a base64 data URI, or an uploaded file. Images can be a public URL or base64, in PNG, JPEG, AVIF, and other formats. `document_url` also accepts PPTX and DOCX. ([basic OCR guide](https://docs.mistral.ai/studio/document-processing/basic_ocr), [API reference](https://docs.mistral.ai/api/endpoint/ocr))

**Limits.** The guide FAQ says: "Uploaded document files must be 50 MB or less and contain 1,000 pages or fewer." ([basic OCR guide](https://docs.mistral.ai/studio/document-processing/basic_ocr), FAQ section, read from the page source) The `pages` parameter selects pages, zero-based, as a list or a range string such as `"0-5"`. ([API reference](https://docs.mistral.ai/api/endpoint/ocr), [changelog 2026-06-23](https://docs.mistral.ai/resources/changelogs)) Rate limits per workspace tier are not stated on the pages that I read. Unverified.

**Output.** The response is JSON with a `pages` array. Each page has `index`, `markdown`, `images`, `tables`, `hyperlinks`, `header`, `footer`, `dimensions`, `confidence_scores`, and `blocks`. Images and tables appear in the Markdown as placeholders such as `![img-0.jpeg](img-0.jpeg)`. `table_format` can be `markdown` or `html`. `include_blocks` returns paragraph-level bounding boxes with a block type, and one block type is `equation` ("A math equation."). `usage_info.pages_processed` reports billed pages. ([basic OCR guide](https://docs.mistral.ai/studio/document-processing/basic_ocr), [API reference](https://docs.mistral.ai/api/endpoint/ocr))

**Math.** The current docs do not state that equations come out as LaTeX. The first Mistral OCR launch post said that it handles "mathematical expressions, tables, and advanced layouts such as LaTeX formatting" and scored 94.29 on its Math benchmark. That claim is for the retired 2503 model. ([Mistral OCR launch](https://mistral.ai/news/mistral-ocr)) The OCR 4 post says that LaTeX strings that render the same can score as a mismatch in benchmarks. This implies LaTeX output, but the post does not promise it. ([OCR 4 launch](https://mistral.ai/news/ocr-4)) Unverified: that OCR 4.1 emits `$...$` and `$$...$$` LaTeX for every equation.

**Price.** The OCR 4 launch post lists $4 per 1,000 pages, $2 per 1,000 pages through the Batch API, and $5 per 1,000 pages for Document AI. ([OCR 4 launch](https://mistral.ai/news/ocr-4)) The OCR 4.1 page lists $4 per 1,000 pages and $5 per 1,000 annotated pages, but it does not make the currency clear. ([OCR 4.1 model page](https://docs.mistral.ai/models/ocr-4-1)) The changelog says that OCR 4.1 has "the same price" as OCR 4.0. ([changelog](https://docs.mistral.ai/resources/changelogs)) A third-party page reports €3.5 per 1,000 pages for 4.1. Unverified, and it conflicts with the primary sources.

**Latency.** No current per-page latency is published. The OCR 4 post gives only customer claims, such as about 4x faster per page than an incumbent. The 2025 launch post claimed "up to 2000 pages per minute on a single node" for the retired model. ([OCR 4 launch](https://mistral.ai/news/ocr-4), [Mistral OCR launch](https://mistral.ai/news/mistral-ocr)) Unverified for OCR 4.1 on the public API.

**Benchmarks.** OCR 4 reported olmOCR-Bench 85.20 and OmniDocBench 93.07. No math-only or arXiv-only number is given. ([OCR 4 launch](https://mistral.ai/news/ocr-4))

## Jina OCR

**Current model.** `jina-ocr-v1` was released on 2026-09-14. It is a 3.4B-parameter mixture-of-experts model with about 570M active parameters, built on DeepSeek-OCR. Its input is a 1024×1024 image. The "Gundam" mode adds tiles up to 1,156 visual tokens per page. ([model page](https://jina.ai/models/jina-ocr-v1), [launch post](https://jina.ai/en-US/news/jina-ocr-v1-faster-document-parsing-on-low-budget-gpus/))

**Endpoints and auth.** Both endpoints use `Authorization: Bearer $JINA_API_KEY`. ([launch post](https://jina.ai/en-US/news/jina-ocr-v1-faster-document-parsing-on-low-budget-gpus/), [Hugging Face card](https://huggingface.co/jinaai/jina-ocr-v1))

1. The OpenAI-compatible endpoint is `POST https://api.jina.ai/v1/chat/completions` with `"model": "jina-ocr-v1"`. It takes one page image as an image URL or a base64 data URI, plus a text prompt. It supports `"stream": true`.
2. The Reader endpoint is `https://r.jina.ai/<url>` with the header `X-Respond-With: jina-ocr-v1`. Reader fetches and renders a page or PDF, then returns Markdown. `X-Page` selects one page of a multi-page document. Reader also accepts a local PDF or HTML file by POST. ([Reader](https://jina.ai/reader))

**Input formats.** The chat endpoint takes page images. The Reader endpoint takes a PDF by URL or by upload, and processes one page per request when `X-Page` is set. No file-size or page-count limit is published. Unverified.

**Output.** The output is Markdown. The default prompt asks for clean Markdown in reading order. The stricter benchmark prompt on the model card asks for LaTeX math with `$...$` and `$$...$$`, no Unicode math symbols, and HTML tables. Math output therefore depends on the prompt that we send. The Reader path does not let us set the prompt, as far as the Reader page shows. Unverified. The model drops page headers and footers. ([Hugging Face card](https://huggingface.co/jinaai/jina-ocr-v1), [model page](https://jina.ai/models/jina-ocr-v1))

**Math benchmarks.** OmniDocBench v1.6 overall is 91.14, with formula CDM 93.28. olmOCR-Bench overall is 83.4, with ArXiv 86.1 and OldScans-Math 82.3. The launch post and the model page disagree on some olmOCR-Bench sub-scores. I took the sub-scores from the model page. ([model page](https://jina.ai/models/jina-ocr-v1), [launch post](https://jina.ai/en-US/news/jina-ocr-v1-faster-document-parsing-on-low-budget-gpus/))

**Latency.** Jina reports 2.57 pages/s and 1,085 output tokens per page on one A100 at concurrency 32. This is self-hosted throughput, not API latency. ([launch post](https://jina.ai/en-US/news/jina-ocr-v1-faster-document-parsing-on-low-budget-gpus/)) The Reader rate-limit table gives an average Reader latency of 7.9 s for all Reader requests, not only OCR. ([Reader](https://jina.ai/reader)) The model card says that a cold start "returns HTTP 503" and suggests a retry after 30 to 60 seconds. ([Hugging Face card](https://huggingface.co/jinaai/jina-ocr-v1))

**Rate limits.** Reader allows 20 RPM with no key, 500 RPM with a free or paid key, and 5,000 RPM with a premium key. ([Reader](https://jina.ai/reader))

**Price.** Jina bills tokens from a prepaid balance. Reader counts the tokens in its output, and the OCR option "Costs 40× more tokens". ([Reader](https://jina.ai/reader)) No price per page is published. `https://jina.ai/pricing` returned HTTP 404 on 2026-10-17. The price per token is not on the primary pages that I could read. Third-party sites report about $0.045 to $0.05 per million tokens. ([markaicode](https://markaicode.com/pricing/jina-ai-pricing/), [usagepricing](https://usagepricing.com/blueprint/jina-ai)) Unverified. With those figures, 1,085 tokens × 40 is about 43,400 billed tokens per page, or about $2 per 1,000 pages through Reader. This is my estimate, not a vendor figure. The billing rule for the chat-completions endpoint is not documented. Unverified.

**License.** The weights are CC BY-NC 4.0, and the card says "Commercial use: contact". This limits self-hosting for a commercial product. It does not by itself limit calls to the paid API. Unverified: whether the API terms allow commercial use of the output. ([Hugging Face card](https://huggingface.co/jinaai/jina-ocr-v1))

## Comparison

| | Mistral OCR 4.1 | Jina `jina-ocr-v1` |
|---|---|---|
| Model id | `mistral-ocr-4-1`, alias `mistral-ocr-latest` | `jina-ocr-v1` |
| Endpoint | `POST /v1/ocr` | `POST /v1/chat/completions`, or Reader `r.jina.ai` |
| Auth | Bearer key | Bearer key |
| Whole PDF in one call | Yes, up to 50 MB and 1,000 pages | Reader only, one page per call with `X-Page` |
| Page images | Yes | Yes (chat endpoint) |
| Output | JSON per page with Markdown, tables, blocks, boxes | Markdown text |
| LaTeX math | Not documented for 4.1 | Yes, when the prompt asks for it |
| Formula benchmark | None published for 4.x | OmniDocBench formula CDM 93.28 |
| Price | $4 per 1,000 pages, $2 batch | Token-based, about $2 per 1,000 pages (estimate, unverified) |
| Published latency | None for the API | 7.9 s average Reader latency, 503 on cold start |

## Fit for the bring-your-own-key flow

Both vendors use one static Bearer key, so storage and use are the same. Our backend must encrypt the key at rest and send it only in the `Authorization` header.

Mistral fits better for four reasons. First, the cost is predictable per page, and `usage_info.pages_processed` lets us show the user what we spent with their key. Second, one call can take a whole PDF with a `pages` range, so we can avoid rasterizing pages first. Third, the response has a stable schema with equation blocks and bounding boxes, and we can map it to our `OCRPage` type. Fourth, the endpoint is documented as generally available, with dated deprecations.

Jina's risks for BYOK are as follows. The user cannot predict the cost per page. Cold starts return 503, so we need retries. The math quality depends on a prompt that only the chat endpoint lets us set. The model license is non-commercial.

## Current code

On `origin/main`, `polytypst/ocr/mistral.py` sends one base64 page image to `mistral-ocr-latest` and reads only `pages[0].markdown`. It does not pin a version, so results change when Mistral moves the alias. `polytypst/ocr/jina.py` on `origin/main` posts a multipart file to `https://r.jina.ai/` with `X-Return-Format: markdown`. It does not set `X-Respond-With: jina-ocr-v1`, so it may not use the OCR model at all. Unverified at run time. The main checkout at `/Users/martinfan/devv/polytypst` has a different `jina.py` and an `engines.py` that are not on `origin/main`. That `jina.py` calls `https://api.jina.ai/v1/chat/completions` with `jina-ocr-v1` and a custom prompt, which matches the documented chat endpoint. Both engines on `origin/main` read the key from the environment or from local files. A BYOK flow must pass the user's key in through the constructor instead.

## Open questions

1. Does OCR 4.1 emit LaTeX for display and inline math on our books? A bake-off on 20 to 30 math pages from Ahlfors and Kodaira would answer this.
2. What exact model-id string does the Mistral API accept for 4.1: `mistral-ocr-4-1` or `mistral-ocr-4-1+2`?
3. What are Mistral's OCR rate limits per workspace tier, and how long does Mistral keep uploaded documents?
4. What does Jina charge per token today, and how does the chat-completions endpoint bill `jina-ocr-v1`?
5. Do Jina's API terms allow commercial use of output from `jina-ocr-v1`, given the CC BY-NC weights?
6. Can a Reader request with `X-Respond-With: jina-ocr-v1` take a custom prompt for LaTeX math?
