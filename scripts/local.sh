#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${KI_TOKEN:?Set KI_TOKEN to a generated token of at least 32 characters}"
export KI_PROVIDER=mock KI_SOURCE=fixture
exec "${VENV:-.venv}/bin/uvicorn" kubeinvestigator.app:create_app --factory --host 127.0.0.1 --port 8080 --no-access-log
