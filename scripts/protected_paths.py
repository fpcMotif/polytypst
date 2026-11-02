"""Stop a commit that changes what the gates measure against, unless its message gives a reason.

Usage:
  uv run python scripts/protected_paths.py --message-file FILE   # git commit-msg hook: the staged changes
  uv run python scripts/protected_paths.py                       # hk check under jj: @ against its parent

The snapshot fixture, the audit baseline and the checker are protected, and so is any edited or deleted
line in an existing test. New test lines are free. A protected change needs this line in the message:
  Protected-change: <why the expected values had to change>
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

PROTECTED = ("tests/fixtures/book_snapshots.json", "quality/baseline.json", "src/checker.py")
REASON = re.compile(r"^Protected-change:[ \t]*\S", re.MULTILINE)


def parse_numstat(text: str) -> list[tuple[int, int, str]]:
    changes = []
    for line in text.splitlines():
        added, deleted, path = line.split("\t", 2)
        binary = added == "-"
        changes.append((1 if binary else int(added), 1 if binary else int(deleted), path))
    return changes


def blocked(changes: list[tuple[int, int, str]], message: str) -> list[str]:
    if REASON.search(message):
        return []
    return [
        path
        for added, deleted, path in changes
        if path in PROTECTED or (path.startswith("tests/") and deleted)
    ]


def run(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--message-file", type=Path, help="the commit message file that git passes to commit-msg")
    args = parser.parse_args()

    if args.message_file:
        message = args.message_file.read_text(encoding="utf-8")
        numstat = run("git", "diff", "--cached", "--numstat")
    elif Path(".jj").is_dir():
        message = run("jj", "log", "--no-graph", "-r", "@", "-T", "description")
        parent, commit = (
            run("jj", "log", "--no-graph", "-r", rev, "-T", "commit_id").strip() for rev in ("@-", "@")
        )
        numstat = run("git", "diff", "--numstat", parent, commit)
    else:
        return 0
    if paths := blocked(parse_numstat(numstat), message):
        print("These changes alter what the gates measure against:", *(f"  {p}" for p in paths), sep="\n")
        print("Add `Protected-change: <reason>` to the commit message (`jj describe` or `git commit`).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
