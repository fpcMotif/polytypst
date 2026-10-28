#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."
canaries=(hecke london_treasury 3_国际经济环境的变化与日本经济)
failed=()
for key in "${canaries[@]}"; do
  scripts/rebuild.sh "$key" || failed+=("$key")
done
if ((${#failed[@]})); then
  echo "canaries failed: ${failed[*]}; logs in output/logs" >&2
  exit 1
fi
