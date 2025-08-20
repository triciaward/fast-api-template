#!/usr/bin/env bash
set -euo pipefail

# Run mypy with SQLAlchemy plugin on representative models
ROOT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
cd "$ROOT_DIR"

if [[ -d "venv" ]]; then
  source venv/bin/activate
fi

python -m mypy \
  --config-file pyproject.toml \
  app/models/core/base.py \
  app/models/auth/user.py \
  app/models/system/audit_log.py

echo "mypy SQLAlchemy check passed"


