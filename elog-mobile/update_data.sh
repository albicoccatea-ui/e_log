#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_FILE="$ROOT_DIR/data/dashboard.json"

python3 "$ROOT_DIR/fetch_endoh_dashboard.py" > "$OUT_FILE"
echo "Updated: $OUT_FILE"
