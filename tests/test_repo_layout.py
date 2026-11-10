import subprocess

from polytypst.paths import ASSETS, OUTPUT, REPO

BINARY_ASSETS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".tif", ".tiff", ".pdf", ".epub", ".zip", ".otf", ".ttf", ".woff", ".woff2"}


def test_output_and_assets_live_outside_the_repository():
    assert not OUTPUT.resolve().is_relative_to(REPO)
    assert not ASSETS.resolve().is_relative_to(REPO)
    assert [name for name in ("output", "scratch", "shitouji", "fonts") if (REPO / name).exists()] == []


def test_git_tracks_no_binary_assets():
    tracked = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    paths = [REPO / name for name in tracked.split("\0") if name]
    assert [str(p.relative_to(REPO)) for p in paths if p.suffix.lower() in BINARY_ASSETS and p.exists()] == []
