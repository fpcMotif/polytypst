import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from polytypst.page_check.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
