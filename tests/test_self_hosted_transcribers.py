import json
import subprocess
import tarfile
from collections.abc import Sequence
from pathlib import Path

import pytest
from conftest import PageRender

from polytypst.ocr import colab, colab_cluster, gpu_worker
from polytypst.ocr.backend import Backend
from polytypst.ocr.cached import CachedTranscriber
from polytypst.ocr.colab_cluster import ClusterStats, ColabOCRCluster
from polytypst.ocr.colab_transcriber import ColabTranscriber
from polytypst.ocr.gemini import GeminiTranscriber
from polytypst.ocr.local_gpu import LocalGpuTranscriber
from polytypst.ocr.openai_compat import OpenAICompatTranscriber
from polytypst.ocr.pages import OCRBackendError, PageImage, Transcript
from polytypst.ocr.transcripts import TranscriptStore


def test_local_worker_gets_explicit_page_numbers_and_its_pages_stream_back(
    page_render: PageRender, monkeypatch: pytest.MonkeyPatch
) -> None:
    pages = [page_render(4), page_render(9, suffix=".jpg")]
    calls: list[list[tuple[int, str]]] = []

    def fake_run_worker(items, out_dir, prompt, num_shards, model_key) -> None:
        calls.append(list(items))
        assert (prompt, num_shards, model_key) == ("P", 2, "deepseek-ocr")
        for n, _ in items:
            gpu_worker.worker_transcript_path(out_dir, n).write_text(f"page {n}")

    monkeypatch.setattr(gpu_worker, "run_worker", fake_run_worker)
    local = LocalGpuTranscriber("deepseek-ocr", "P", 2, "local:deepseek-ocr")
    assert list(local.transcribe(pages)) == [
        Transcript(4, "page 4"),
        Transcript(9, "page 9"),
    ]
    assert calls == [[(4, str(pages[0].path)), (9, str(pages[1].path))]]


def test_local_worker_pages_finished_before_a_crash_still_arrive(
    page_render: PageRender, monkeypatch: pytest.MonkeyPatch
) -> None:
    pages = [page_render(1), page_render(2)]

    def dying_worker(items, out_dir, prompt, num_shards, model_key) -> None:
        gpu_worker.worker_transcript_path(out_dir, 1).write_text("page 1")
        raise RuntimeError("CUDA out of memory")

    monkeypatch.setattr(gpu_worker, "run_worker", dying_worker)
    stream = LocalGpuTranscriber("jina-ocr-v1", "P", 1, "local:jina-ocr-v1").transcribe(
        pages
    )
    assert next(stream) == Transcript(1, "page 1")
    with pytest.raises(RuntimeError, match="out of memory"):
        _ = next(stream)


class FakeCluster(ColabOCRCluster):
    def __init__(self) -> None:
        super().__init__()
        self.batches: list[list[int]] = []

    def run_cluster(self, pages: Sequence[PageImage], out_dir: Path) -> ClusterStats:
        batch = [p.number for p in pages]
        self.batches.append(batch)
        for n in batch:
            gpu_worker.worker_transcript_path(out_dir, n).write_text(f"Colab page {n}.")
        return ClusterStats(len(batch), len(batch), 0.0, 0.0, 1)


def test_colab_runs_pages_in_batches_and_yields_each_batch(
    page_render: PageRender,
) -> None:
    pages = [page_render(n) for n in (1, 3, 4)]
    cluster = FakeCluster()
    got = list(ColabTranscriber(cluster, 2, "colab:jina-ocr-v1").transcribe(pages))
    assert cluster.batches == [[1, 3], [4]]
    assert got[-1] == Transcript(4, "Colab page 4.")


@pytest.fixture
def fake_vms(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    vms: dict[str, list[str]] = {"started": [], "stopped": [], "broken": []}

    class FakeSession:
        def __init__(self, name: str, gpu: str) -> None:
            self.name = name
            self.pages: list[str] = []

        def start(self) -> bool:
            vms["started"].append(self.name)
            return self.name not in vms["broken"]

        def install(self, packages: tuple[str, ...]) -> bool:
            return True

        def upload(self, local: Path, remote: str) -> bool:
            if remote == "/content/pages.tar.gz":
                with tarfile.open(local) as tar:
                    self.pages = tar.getnames()
            return True

        def exec(self, code: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
            done = json.dumps({"done": True, "alive": True, "pages": 0, "log": ""})
            return subprocess.CompletedProcess([], 0, done if code == colab_cluster.POLL_CODE else "", "")

        def download(self, remote: str, local: Path) -> bool:
            if remote != "/content/markdown.tar.gz":
                return False
            made = local.parent / f"{self.name}-md"
            made.mkdir(exist_ok=True)
            with tarfile.open(local, "w:gz") as tar:
                for name in self.pages:
                    md = made / f"{Path(name).stem}.md"
                    _ = md.write_text(f"{name} on {self.name}")
                    tar.add(md, arcname=md.name)
            return True

        def stop(self) -> None:
            vms["stopped"].append(self.name)

    monkeypatch.setattr(colab_cluster, "ColabSession", FakeSession)
    monkeypatch.setattr(colab_cluster, "POLL_SEC", 0)
    return vms


def test_colab_vms_start_once_for_every_batch_and_stop_at_the_end(
    page_render: PageRender, fake_vms: dict[str, list[str]]
) -> None:
    pages = [page_render(n) for n in range(1, 7)]
    cluster = ColabOCRCluster(num_workers=2)
    got = list(ColabTranscriber(cluster, 2, "colab:jina-ocr-v1").transcribe(pages))
    assert [t.number for t in got] == [1, 2, 3, 4, 5, 6]
    assert sorted(fake_vms["started"]) == cluster.session_names(2)
    assert sorted(fake_vms["stopped"]) == cluster.session_names(2)


def test_a_vm_that_fails_to_start_hands_its_pages_to_the_others(
    tmp_path: Path,
    page_render: PageRender,
    fake_vms: dict[str, list[str]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    cluster = ColabOCRCluster(num_workers=2)
    broken, healthy = cluster.session_names(2)
    fake_vms["broken"].append(broken)
    stats = cluster.run_cluster([page_render(n) for n in range(1, 5)], tmp_path)
    assert sorted(p.name for p in tmp_path.glob("p_*.md")) == [f"p_00{n}.md" for n in range(1, 5)]
    assert stats.completed_pages == 4
    assert f"[{broken}] Dropped: the VM did not start. Its 2 pages go to the other VMs." in capsys.readouterr().out
    assert sorted(fake_vms["stopped"]) == [broken, healthy]


def test_colab_archive_names_pages_by_number_whatever_the_file_is_called(
    tmp_path: Path, page_render: PageRender
) -> None:
    odd = page_render(2, suffix=".jpg").path.rename(tmp_path / "IMG_7731.jpg")
    archive = ColabOCRCluster.pack_archive(
        [PageImage(2, odd)], tmp_path / "pages.tar.gz"
    )
    with tarfile.open(archive) as tar:
        assert tar.getnames() == ["p_002.jpg"]


def test_worker_page_items_read_jpeg_renders_too(
    tmp_path: Path, page_render: PageRender
) -> None:
    for page in (page_render(1), page_render(2, suffix=".jpeg")):
        _ = page.path.rename(tmp_path / page.path.name)
    assert [n for n, _ in gpu_worker.page_items(tmp_path)] == [1, 2]


def test_cached_serves_only_the_pages_its_store_has(
    tmp_path: Path, page_render: PageRender
) -> None:
    _ = (tmp_path / "p_001.md").write_text("Cached page one text.\n")
    cached = CachedTranscriber(TranscriptStore(tmp_path), "cached")
    got = list(cached.transcribe([page_render(1), page_render(2)]))
    assert got == [Transcript(1, "Cached page one text.\n")]


def test_backend_builds_api_transcribers_with_their_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "g")
    monkeypatch.setenv("JINA_API_KEY", "j")
    gemini = Backend.parse("gemini").transcriber("Book prompt.")
    assert isinstance(gemini, GeminiTranscriber)
    assert gemini.provenance == Backend.parse("gemini").provenance("Book prompt.")
    jina = Backend.parse("jina").transcriber(None)
    assert isinstance(jina, OpenAICompatTranscriber)
    assert jina.url == "https://api.jina.ai/v1/chat/completions"
    assert jina.pace_sec == 1.5
    local_server = Backend.parse(
        "openai:qwen?base_url=http://box:8000/v1&key_env="
    ).transcriber(None)
    assert isinstance(local_server, OpenAICompatTranscriber)
    assert local_server.headers == {}


def test_backend_without_its_key_fails_before_any_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(OCRBackendError, match="MISTRAL_API_KEY"):
        _ = Backend.parse("mistral").transcriber(None)


def test_colab_without_its_cli_fails_and_names_the_local_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(colab.shutil, "which", lambda _name: None)
    with pytest.raises(OCRBackendError, match="--backend local:unlimited-ocr"):
        _ = Backend.parse("colab:unlimited-ocr").transcriber(None)


def test_backend_builds_self_hosted_and_cached_transcribers(tmp_path: Path) -> None:
    local = Backend.parse("local:qwen3-vl-8b?shards=2").transcriber("Book prompt.")
    assert isinstance(local, LocalGpuTranscriber)
    assert (local.model, local.prompt, local.shards) == (
        "qwen3-vl-8b",
        "Book prompt.",
        2,
    )
    cached = Backend.parse(f"cached:?dir={tmp_path}").transcriber(None)
    assert isinstance(cached, CachedTranscriber)
    assert cached.source.directory == tmp_path


def test_two_runs_with_the_same_session_option_name_different_vms() -> None:
    first, second = ColabOCRCluster(session_prefix="ocr"), ColabOCRCluster(session_prefix="ocr")
    names = first.session_names(2)
    assert len(set(names)) == 2
    assert all(name.startswith("ocr-") for name in names)
    assert set(names).isdisjoint(second.session_names(2))
