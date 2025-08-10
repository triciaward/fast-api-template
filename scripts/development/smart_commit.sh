#!/usr/bin/env bash

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"commit message\""
  exit 1
fi

COMMIT_MSG="$1"

# Stage everything by default
git add -A

# If pre-commit is available, run it first so fixes land in the same commit
if command -v pre-commit >/dev/null 2>&1; then
  echo "🔍 Running pre-commit hooks (first pass)..."
  if ! pre-commit run --all-files --hook-stage commit; then
    echo "⚠️  Hooks reported issues; attempting to stage auto-fixes and retry once..."
    git add -A
    # Retry hooks once to catch formatting/auto-fixers on the second pass
    pre-commit run --all-files --hook-stage commit || {
      echo "❌ Pre-commit hooks still failing. Please fix remaining issues and retry."
      exit 1
    }
  fi
  # Commit without re-running hooks to avoid duplicate runs
  echo "✅ Hooks passed. Creating commit without re-running hooks..."
  git commit -m "$COMMIT_MSG" --no-verify
else
  echo "ℹ️  pre-commit not found. Creating commit directly..."
  git commit -m "$COMMIT_MSG"
fi

echo "✅ Commit created with preserved message."


