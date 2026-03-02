#!/usr/bin/env bash
# Syncs frontend/src/ into demo/src/, preserving demo-only files and patches.
# Run from the repo root:  bash demo/sync.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND="$REPO_ROOT/frontend/src"
DEMO="$REPO_ROOT/demo/src"

if [ ! -d "$FRONTEND" ]; then
  echo "Error: frontend/src not found at $FRONTEND" >&2
  exit 1
fi

# 1. Stash demo-only files
DEMO_ONLY=(
  "api.js"
  "api-mock.js"
  "components/DemoBanner.jsx"
  "data/bays.json"
)

TMP=$(mktemp -d)
for f in "${DEMO_ONLY[@]}"; do
  if [ -f "$DEMO/$f" ]; then
    mkdir -p "$TMP/$(dirname "$f")"
    cp "$DEMO/$f" "$TMP/$f"
  fi
done

# 2. Copy frontend/src/ wholesale (overwrites everything except demo-only)
rsync -a --delete \
  --exclude='test-setup.js' \
  "$FRONTEND/" "$DEMO/"

# 3. Restore demo-only files
for f in "${DEMO_ONLY[@]}"; do
  if [ -f "$TMP/$f" ]; then
    mkdir -p "$DEMO/$(dirname "$f")"
    cp "$TMP/$f" "$DEMO/$f"
  fi
done
rm -rf "$TMP"

# 4. Patch App.jsx — add DemoBanner import and component
APP="$DEMO/App.jsx"
if ! grep -q 'DemoBanner' "$APP"; then
  # Add import after ErrorBoundary import
  sed -i '' "/import ErrorBoundary/a\\
import DemoBanner from './components/DemoBanner'
" "$APP"

  # Add <DemoBanner /> after <ErrorBoundary>
  sed -i '' 's|<ErrorBoundary>|<ErrorBoundary>\
    <DemoBanner />|' "$APP"
fi

# 5. Sync bays.json from backend
BAYS_SRC="$REPO_ROOT/backend/data/bays.json"
if [ -f "$BAYS_SRC" ]; then
  mkdir -p "$DEMO/data"
  cp "$BAYS_SRC" "$DEMO/data/bays.json"
fi

echo "Demo synced from frontend/src successfully."
