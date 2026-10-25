import os
from pathlib import Path

BOOKS_ENV = "POLYTYPST_BOOKS"


class BookStateError(RuntimeError):
    pass


def book_state(out_dir: Path) -> Path:
    root = os.environ.get(BOOKS_ENV)
    if not root:
        raise BookStateError(
            f"set {BOOKS_ENV} (environment or mise.local.toml) to the folder that holds each book's state"
        )
    return Path(root).expanduser() / Path(out_dir).name
