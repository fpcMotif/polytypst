#!/usr/bin/env bash
# Downloads fonts needed for builds (kept out of git).
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
fonts="${POLYTYPST_ASSETS:-$repo/../polytypst-assets}/fonts"
mkdir -p "$fonts"
fetch() {
  [ -f "$fonts/$1" ] || curl -fL -o "$fonts/$1" "$2"
}
noto=https://github.com/notofonts/noto-cjk/raw/main/Serif/SubsetOTF/SC
for w in Regular SemiBold Bold; do
  fetch "NotoSerifSC-$w.otf" "$noto/NotoSerifSC-$w.otf"
done
ofl=https://github.com/google/fonts/raw/main/ofl
fetch Baskervville-wght.ttf "$ofl/baskervville/Baskervville%5Bwght%5D.ttf"
fetch Baskervville-Italic-wght.ttf "$ofl/baskervville/Baskervville-Italic%5Bwght%5D.ttf"
fetch LibreBaskerville-wght.ttf "$ofl/librebaskerville/LibreBaskerville%5Bwght%5D.ttf"
fetch LibreBaskerville-Italic-wght.ttf "$ofl/librebaskerville/LibreBaskerville-Italic%5Bwght%5D.ttf"
for w in Regular Semibold Bold; do
  fetch "SourceSans3-$w.otf" "https://github.com/adobe-fonts/source-sans/raw/release/OTF/SourceSans3-$w.otf"
done
for w in Regular It Semibold SemiboldIt Bold BoldIt; do
  fetch "SourceSerif4-$w.otf" "https://github.com/adobe-fonts/source-serif/raw/release/OTF/SourceSerif4-$w.otf"
done
