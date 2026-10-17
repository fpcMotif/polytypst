# Colab self-host: how the web backend reaches the operator's Colab GPU

Ticket: devv-9n0w. Researched 2026-10-17.

## Answer

Do not open an inbound tunnel to Colab. Run the OCR worker on Colab as a **pull worker**: it makes outbound HTTPS calls to a Convex HTTP action, leases a job, fetches page images, and posts transcripts back. The operator starts and stops the VM with the official `colab` CLI, which polytypst already wraps in `ColabSession`. This needs no tunnel, no public endpoint on the VM, and no browser tab.

The transport choice does not settle the bigger risk. The Colab terms forbid giving "direct or indirect access to Colab to any third party" ([Colab Terms, v6, last modified 2026-08-13](https://research.google.com/colaboratory/tos_v6.html)). An invite-only service that runs other people's documents on the operator's consumer Colab account plausibly falls under that clause, whatever the transport. Until someone resolves that, use the operator's Colab only for the operator's own documents. Give invited users their own Jina or Mistral key, or a GPU host billed under Google Cloud terms, such as [Colab Enterprise](https://cloud.google.com/colab/docs/introduction).

## How polytypst connects today

All four files live in the main checkout at `polytypst/ocr/` and are untracked there. `origin/main` has older siblings instead (`colab_runner.py`, `dual_colab.py`).

- `colab.py` wraps the official Google `colab` CLI ([googlecolab/google-colab-cli](https://github.com/googlecolab/google-colab-cli), Apache-2.0, installed here as v0.7.4). `ColabSession` shells out to `colab new --session NAME --gpu GPU`, `install`, `exec` (code on stdin), `upload`, `download`, `ls`, and `stop`. Uploads are split into 25 MB chunks because "larger Jupyter payloads fail with HTTP 400". `account_usage()` parses `colab usage` for the compute-unit balance.
- `colab_cluster.py` (`ColabOCRCluster`) packs pages into a tarball, starts N VMs in parallel, uploads the tarball plus `ocr_models.py` and `gpu_worker.py`, and launches `python -m ocrpkg.gpu_worker` with `subprocess.Popen` inside the kernel. It then polls every 15 s (`POLL_SEC`) with `colab exec`, reading `/content/worker.pid` and the transcript count. On completion, timeout, or a dead worker it downloads `markdown.tar.gz`, and the `with session:` block always calls `colab stop`. `ColabOCREngine` feeds it batches of 70 pages and resumes by skipping pages that already have transcripts.
- `gpu_worker.py` runs on the VM. It loads one model (Jina via transformers, DeepSeek `infer`, or vLLM chat), shards pages across model copies, writes `p_NNN.md` per page and `_stats.json`, and tars the output.
- `colab_cli.py` is the `polytypst-colab` command: GPU catalog, `usage`, `probe`, and `bench`.

So today the **operator's machine** is the control plane. Every byte moves through the `colab` CLI from a local process. The CLI talks to `https://colab.research.google.com/tun/m/assign` to get a VM and a runtime-proxy URL and token. It then uses the Jupyter kernel and contents APIs through that proxy (`colab_cli/client.py`, `colab_cli/runtime.py`). The CLI refreshes the runtime-proxy token five minutes before expiry (`TOKEN_REFRESH_MARGIN` in `colab_cli/common.py`) and stores session state in `~/.config/colab-cli/sessions.json`.

Nothing in `web/` reaches Colab yet. `web/convex/` has only `books.ts` and `schema.ts`, and `web/wrangler.jsonc` serves static assets only.

## Constraint from the backend side

Neither Convex nor a Cloudflare Worker can hold a Colab session. The CLI is a Python program with local state and an OAuth login. Convex actions are bounded (Convex runtime 30 min, Node runtime 10 min, per [Convex limits](https://docs.convex.dev/production/state/limits)). Something long-lived must therefore own the VM: the operator's machine, or the VM itself. Convex can receive calls through [HTTP actions](https://docs.convex.dev/functions/http-actions) and can make outbound `fetch` calls from actions. Either direction is possible, so the question is which side dials.

## Options compared

| | Pull worker (recommended) | cloudflared tunnel | ngrok tunnel | colab-ssh | Colab MCP browser connection |
|---|---|---|---|---|---|
| Direction | VM dials Convex (outbound HTTPS) | Convex dials VM through Cloudflare | Convex dials VM through ngrok | Operator dials VM sshd through cloudflared or ngrok | Browser tab dials a localhost WebSocket |
| Setup | Add a Convex job table, HTTP actions, and a shared secret. Add a poll loop to `gpu_worker.py`. Start the VM with `colab new` or `colab run`. | Quick tunnel: none. Named tunnel: Cloudflare account, domain, tunnel token, and Access policy. | Account and authtoken. The free plan gives one static dev domain. | `pip install colab_ssh` in a notebook, plus client config. | Add the MCP server to a local agent. It opens `colab.research.google.com/notebooks/empty.ipynb` in a browser. |
| Session lifetime | The VM lifetime | The VM lifetime | The VM lifetime | The VM lifetime | The browser tab lifetime |
| Reconnect | Leases expire and jobs re-queue. A new VM resumes by polling. | A quick tunnel gets a new URL on every start. A named tunnel keeps its hostname. | The dev domain is static. The agent must restart on the new VM. | New tunnel and new host each time | A human must reopen the tab. The server waits 60 s for the tab (`UI_CONNECTION_TIMEOUT`). |
| Throughput limits | Only Convex and VM bandwidth. Not measured here. | Quick tunnel: 200 in-flight requests, then 429. | Free plan: 1 GB outbound data and 20,000 HTTP requests per month. | Not a job transport | Not a job transport |
| Colab policy | Outbound HTTPS from a kernel job. No listed restriction. | Exposes a web service from the VM. See below. | Same as cloudflared | The project README warns that Colab prohibited SSH. | Interactive use in a notebook, as Colab intends |

### Pull worker

The VM runs a loop: `POST /ocr/lease` returns a job id and signed image URLs, the worker transcribes, and `POST /ocr/complete` stores the Markdown. A lease has a deadline. When a VM dies, its leases lapse and another worker takes the job. That replaces today's 15 s `colab exec` polling and the tarball round trip. It also removes the operator's laptop from the data path, though the operator still starts the VM. Colab's own CLI documents that "sessions stay alive as long as the kernel is active" (bundled README, "Activity-Based Liveness"), so a busy loop keeps the VM alive until the hard cap.

### Tunnels (cloudflared, ngrok)

A tunnel lets Convex call an HTTP server on the VM. Cloudflare states that quick tunnels "are for testing and development", have "no uptime guarantee", support "up to 200 in-flight requests", and do not support Server-Sent Events ([Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)). A named tunnel needs an account and a domain ([Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/)). It can be gated with [Access service tokens](https://developers.cloudflare.com/cloudflare-one/identity/service-tokens/) so that only Convex can call it. ngrok's free plan caps data at 1 GB outbound and 20,000 HTTP requests per month, and has no endpoint timeout ([ngrok free plan limits](https://ngrok.com/docs/pricing-limits/free-plan-limits/)).

The policy problem is the endpoint itself. Colab disallows on **all** managed runtimes "file hosting, media serving, or other web service offerings not related to interactive compute with Colab" and "connecting to remote proxies" ([Colab FAQ](https://research.google.com/colaboratory/faq.html)). An OCR HTTP API on a public tunnel hostname is a web service offering. Whether a tunnel client counts as a "remote proxy" is not defined. Either reading makes a tunnel the riskiest option.

### colab-ssh

[WassimBenzarti/colab-ssh](https://github.com/WassimBenzarti/colab-ssh) starts sshd in the notebook and exposes it with cloudflared or ngrok. Its README says "Google Colab recently prohibited the usage of SSH on their platform". The last push was 2024-11-08. The FAQ lists "remote control such as SSH shells" as disallowed on free runtimes and on paid runtimes "without a positive Colab compute unit balance". A paid plan with a positive balance lifts that restriction. The official CLI now offers `colab ssh`, which needs no tunnel. It connects to `wss://<runtime-proxy>/colab/ssh` with the runtime-proxy token, sends an Ed25519 or ECDSA public key in the `X-Colab-Ssh-Pubkey` header, and allows one SSH client per runtime (HTTP 429 otherwise) (`colab_cli/commands/ssh.py`). SSH is an operator shell, not a job transport, so neither form answers the backend question.

### Colab MCP browser connection

[googlecolab/colab-mcp](https://github.com/googlecolab/colab-mcp) bridges a **local** agent to a notebook open in the browser. Its server listens on `localhost` on a random port with a random token. It opens `https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=…&mcpProxyPort=…` and accepts only the Colab origins (`src/colab_mcp/websocket_server.py`, `session.py`). The README requires a client that "is running locally on your device". It ends when the tab closes. A server-side backend cannot use it.

## Session lifetime facts

From the [Colab FAQ](https://research.google.com/colaboratory/faq.html):

- "Runtimes will time out if you are idle." The FAQ gives no idle duration.
- "In general, notebooks can run for at most 12 hours", and paid plans end at backend termination "if you exhaust your available compute units".
- "Colab Pro+ supports continuous code execution for up to 24 hours if you have sufficient compute units. Idle timeouts only apply if code execution terminates."
- Free runtimes and runtimes without a positive compute-unit balance "may be terminated at any time without warning". On those runtimes "running distributed computing workers" is also disallowed. That would cover a pull worker on a free account, so the operator account must keep a positive balance.

Every option therefore needs a job queue that survives VM loss. The pull worker's lease design provides one directly.

## Open questions

1. Does running invited users' documents on the operator's consumer Colab breach "provide direct or indirect access to Colab to any third party"? This needs a decision by the operator, or legal advice. It decides whether operator-Colab can be the default backend at all.
2. Should the default backend for invited users move to Colab Enterprise or another Google Cloud GPU, which run under Cloud terms? Colab Enterprise pricing and its GPU availability (G4, H100) were not checked here.
3. Who starts the VM when a job arrives while no worker is running? The options are a manual operator step, a cron job on the operator's machine that runs `colab new` when the Convex queue is non-empty, or `colab run` per batch. Convex cannot run the CLI itself.
4. Throughput was not measured. Compare one 70-page batch through today's CLI path with the same batch over direct Convex fetches before committing to the change.
5. Convex storage limits on the plan in use (1 GB free) cap how many page images can wait in the queue. Confirm whether R2 should hold the images instead.
6. The four files in `polytypst/ocr/` are untracked in the main checkout. They should land on `main` before the pull worker builds on them.
