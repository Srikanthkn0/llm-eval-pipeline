#!/usr/bin/env bash
# Local dev. Render uses gunicorn (see DEPLOYMENT.md).
set -euo pipefail
cd "$(dirname "$0")"

if [[ -d venv ]]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

PORT="${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload --reload-dir app