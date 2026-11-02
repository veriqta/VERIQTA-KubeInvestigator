#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
suite=${KI_ACCEPTANCE_SUITE:-smoke}
case "$suite" in smoke|recovery) ;; *) echo "Unsupported acceptance suite" >&2; exit 2;; esac
result_file=".data/$suite-result.json"
missing=()
for tool in docker kind kubectl helm; do
  command -v "$tool" >/dev/null || missing+=("$tool")
done
if ((${#missing[@]})); then
  echo "BLOCKED: missing required tools: ${missing[*]}" >&2
  exit 2
fi
# Check local configuration before contacting a daemon; never use a remote runtime.
smoke_docker_endpoint=${DOCKER_HOST:-}
if [[ -z "$smoke_docker_endpoint" ]]; then
  smoke_docker_endpoint=$(docker context inspect --format '{{.Endpoints.docker.Host}}')
fi
case "$smoke_docker_endpoint" in
  unix:///*) ;;
  *) echo "BLOCKED: select a local Unix-socket Docker runtime; remote runtimes are not supported by this test" >&2; exit 2 ;;
esac
export KIND_EXPERIMENTAL_PROVIDER=docker
if ! docker info >/dev/null 2>&1; then
  echo "BLOCKED: Docker daemon is unavailable or permission was denied" >&2
  exit 2
fi
if [[ ! -x "${VENV:-.venv}/bin/python" ]]; then
  echo "BLOCKED: run make setup with Python 3.12+ first" >&2
  exit 2
fi
# Isolate installer credentials and context changes from every existing kubeconfig.
umask 077
smoke_scratch=$(mktemp -d "${TMPDIR:-/tmp}/veriqta-smoke.XXXXXX")
export KUBECONFIG="$smoke_scratch/kubeconfig"
touch "$KUBECONFIG"
clusters=$(kind get clusters) # Do not treat a failed inventory as an empty inventory.
if grep -qx veriqta-investigator-demo <<< "$clusters"; then
  echo "Demo name is occupied; refusing to reuse or delete it" >&2
  rm -rf "$smoke_scratch"
  exit 1
fi
# The name was unoccupied. Explicit kind cleanup does not depend on current context.
cleanup() {
  status=$?
  trap - EXIT
  if [[ "$status" != 0 ]]; then
    mkdir -p .capture
    kubectl --context kind-veriqta-investigator-demo -n veriqta-system get pods,pvc --request-timeout=10s > .capture/smoke-failure-status.log 2>&1 || true
    kubectl --context kind-veriqta-investigator-demo -n veriqta-system logs deployment/investigator --tail=100 --request-timeout=10s > .capture/smoke-failure-startup.log 2>&1 || true
  fi
  cleaned=true
  if ! kind delete cluster --name veriqta-investigator-demo; then
    echo "Cleanup failed for the disposable test cluster" >&2
    status=1
    cleaned=false
  fi
  if [[ "$cleaned" = true ]]; then
    remaining=$(kind get clusters) || { status=1; cleaned=false; }
    if grep -qx veriqta-investigator-demo <<< "$remaining"; then status=1; cleaned=false; fi
  fi
  if [[ -f "$result_file" ]]; then
    "${VENV:-.venv}/bin/python" - "$status" "$cleaned" "$result_file" <<'PYRESULT'
import json,sys
from pathlib import Path
p=Path(sys.argv[3])
r=json.loads(p.read_text())
r['cluster_cleanup_verified']=sys.argv[2]=='true'
r['status']='passed' if sys.argv[1]=='0' and r['cluster_cleanup_verified'] else 'failed'
p.write_text(json.dumps(r,indent=2)+'\n')
PYRESULT
  fi
  rm -f .data/demo-access.env .data/smoke-owned
  rm -rf "$smoke_scratch"
  exit "$status"
}
mkdir -p .data
touch .data/smoke-owned
rm -f "$result_file"
trap cleanup EXIT
bash scripts/demo.sh setup
"${VENV:-.venv}/bin/python" "scripts/$suite.py"
