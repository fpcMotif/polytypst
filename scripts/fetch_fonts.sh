#!/usr/bin/env bash
# Downloads fonts needed for builds (kept out of git).
set -euo pipefail
cd "$(dirname "$0")/../fonts"
base=https://github.com/notofonts/noto-cjk/raw/main/Serif/OTF/SimplifiedChinese
for w in Regular SemiBold Bold; do
  f=NotoSerifSC-$w.otf
  [ -f "$f" ] || curl -fL -o "$f" "$base/$f"
done
