#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cluster=veriqta-investigator-demo
context=kind-veriqta-investigator-demo
mode=${1:-setup}
kc() { kubectl --context "$context" "$@"; }
check_context() {
  test "$(kubectl config current-context)" = "$context" || { echo "Refusing unrelated context" >&2; exit 1; }
}
case "$mode" in
  setup)
    for tool in docker kind kubectl helm python3; do command -v "$tool" >/dev/null || { echo "Missing $tool"; exit 1; }; done
    clusters=$(kind get clusters)
    if grep -qx "$cluster" <<< "$clusters"; then echo "Demo cluster already exists; refusing to reuse it"; exit 1; fi
    kind create cluster --name "$cluster" --image "${KI_KIND_IMAGE:-kindest/node:v1.35.8@sha256:07b2536e30b803ed61d1677a79df6115f798ce64c80f9e22f6ed45afd09323c0}" --wait 180s
    check_context
    docker build -t kubeinvestigator:0.1.0 .
    kind load docker-image kubeinvestigator:0.1.0 --name "$cluster"
    kc apply -f examples/failures.yaml
    kc create namespace veriqta-system
    mkdir -p .data
    umask 077
    python3 -c 'import secrets; print("KI_TOKEN="+secrets.token_urlsafe(32))' > .data/demo-access.env
    kc -n veriqta-system create secret generic investigator-access --from-env-file=.data/demo-access.env
    helm upgrade --install investigator charts/kubeinvestigator --kube-context "$context" -n veriqta-system -f examples/values.yaml --wait --timeout 180s
    kc -n veriqta-demo wait --for=condition=Ready pod/frontend --timeout=120s
    kc -n veriqta-demo wait --for=jsonpath='{.status.containerStatuses[0].state.waiting.reason}'=CrashLoopBackOff pod/checkout-crash --timeout=180s
    kc -n veriqta-demo wait --for=jsonpath='{.status.containerStatuses[0].state.waiting.reason}'=ImagePullBackOff pod/catalog-image --timeout=180s
    echo "Ready. Token is in .data/demo-access.env (keep private)."
    echo "Run: kubectl --context $context -n veriqta-system port-forward --address 127.0.0.1 svc/investigator 8080:8080"
    ;;
  correct-service)
    check_context
    kc -n veriqta-demo patch service frontend --type merge -p '{"spec":{"selector":{"app":"frontend"}}}'
    kc -n veriqta-demo wait --for=jsonpath='{.endpoints[0].conditions.ready}'=true endpointslice -l kubernetes.io/service-name=frontend --timeout=120s
    ;;
  correct-image)
    check_context
    kc -n veriqta-demo set image pod/catalog-image app=busybox:1.37.0
    kc -n veriqta-demo wait --for=condition=Ready pod/catalog-image --timeout=180s
    ;;
  correct-crash)
    check_context
    kc -n veriqta-demo delete pod checkout-crash --wait=true
    kc -n veriqta-demo run checkout-crash --image=busybox:1.37.0 --labels=app=checkout --command -- sh -c 'sleep 86400'
    kc -n veriqta-demo wait --for=condition=Ready pod/checkout-crash --timeout=120s
    ;;
  cleanup)
    check_context
    kind delete cluster --name "$cluster"
    rm -f .data/demo-access.env
    ;;
  *) echo "Usage: $0 setup|correct-service|correct-image|correct-crash|cleanup"; exit 2 ;;
esac
