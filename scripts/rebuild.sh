#!/usr/bin/env bash
# Rebuilds one book (pdf,tex), then audits it, each step under a time limit.
# Usage: scripts/rebuild.sh KEY   Logs: output/logs/KEY.{build,audit}.log
# REBUILD_TIMEOUT sets the limit per step in seconds (default 900); a step that hits it exits 124.
set -uo pipefail
cd "$(dirname "$0")/.."
key=$1
limit=${REBUILD_TIMEOUT:-900}
logs=output/logs
mkdir -p "$logs"
timeout -k 30 "$limit" mise exec -- uv run polytypst build "$key" --formats pdf,tex >"$logs/$key.build.log" 2>&1
build=$?
timeout -k 30 "$limit" mise exec -- uv run polytypst audit "$key" --edition monograph >"$logs/$key.audit.log" 2>&1
audit=$?
echo "$key: build exit $build, audit exit $audit: $(head -1 "$logs/$key.audit.log")"
if ((build)); then
  exit "$build"
fi
exit "$audit"
