#!/usr/bin/env bash

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"commit message\""
  exit 1
fi

COMMIT_MSG="$1"

# Stage everything by default
git add -A

# If pre-commit is available, run fixers first so auto-fixes are included
if command -v pre-commit >/dev/null 2>&1; then
  echo "🔧 Running formatter/linter fixers before commit..."
  # Run only fixer hooks; ignore their exit codes, then re-stage
  pre-commit run --hook-stage commit ruff || true
  pre-commit run --hook-stage commit black || true
  git add -A
fi

# Now do a normal commit so full hooks (incl. mypy) run on staged files only
set +e
git commit -m "$COMMIT_MSG"
COMMIT_EXIT=$?
set -e

if [ $COMMIT_EXIT -ne 0 ]; then
  echo "❌ Commit failed (likely due to non-fixable hook errors). Please address and re-run."
  exit $COMMIT_EXIT
fi

echo "✅ Commit created with preserved message."


