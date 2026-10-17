#!/bin/sh
# Keep OCR API keys in the macOS Keychain; .env.schema reads them with `security`.
set -eu

NAMES="MISTRAL_API_KEY JINA_API_KEY"
ROOT=$(cd "$(dirname "$0")/.." && pwd)
ENV_FILES="$ROOT/.env.local $ROOT/web/.env.local"

store() {
  security add-generic-password -U -s "polytypst.$1" -a "$USER" -w "$2"
}

case "${1:-}" in
  import)
    for name in $NAMES; do
      value=""
      for file in $ENV_FILES; do
        [ -f "$file" ] || continue
        found=$(awk -F= -v k="$name" '$1 == k { sub(/^[^=]*=/, ""); print; exit }' "$file")
        [ -n "$found" ] && value=$found
      done
      if [ -n "$value" ]; then
        store "$name" "$value"
        echo "$name: stored in Keychain"
      else
        echo "$name: not found in .env.local, skipped"
      fi
    done
    for file in $ENV_FILES; do
      [ -f "$file" ] || continue
      awk -F= '$1 != "MISTRAL_API_KEY" && $1 != "JINA_API_KEY"' "$file" > "$file.tmp"
      mv "$file.tmp" "$file"
      echo "$file: key lines removed"
    done
    ;;
  set)
    name=${2:?usage: ocr-keys.sh set MISTRAL_API_KEY|JINA_API_KEY}
    printf '%s value (hidden): ' "$name"
    stty -echo
    read -r value
    stty echo
    echo
    store "$name" "$value"
    echo "$name: stored in Keychain"
    ;;
  clear)
    for name in $NAMES; do
      security delete-generic-password -s "polytypst.$name" >/dev/null 2>&1 \
        && echo "$name: deleted from Keychain" || echo "$name: not in Keychain"
    done
    ;;
  status)
    for name in $NAMES; do
      security find-generic-password -s "polytypst.$name" >/dev/null 2>&1 \
        && echo "$name: in Keychain" || echo "$name: missing"
    done
    ;;
  *)
    echo "usage: scripts/ocr-keys.sh import|set NAME|clear|status" >&2
    exit 2
    ;;
esac
