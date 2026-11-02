#!/usr/bin/env bash
# Download checksum-verified kind, matching kubectl and the tested Helm release.
set -euo pipefail
version=${1:-v1.35.8}
bin_dir=${2:-"$PWD/.capture/tools/bin"}
[[ "$version" =~ ^v1\.[0-9]+\.[0-9]+$ ]] || { echo "Expected Kubernetes version v1.MINOR.PATCH" >&2; exit 2; }
case "$(uname -s)" in Linux) platform=linux;; Darwin) platform=darwin;; *) echo "Use Linux, macOS or WSL2" >&2; exit 2;; esac
case "$(uname -m)" in x86_64|amd64) arch=amd64;; arm64|aarch64) arch=arm64;; *) echo "Unsupported CPU architecture" >&2; exit 2;; esac
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$bin_dir"
bin_dir=$(cd "$bin_dir" && pwd)
cd "$scratch"
fetch() { curl --fail --silent --show-error --location --retry 2 --connect-timeout 10 --max-time 180 "$1" -o "$2"; }
fetch "https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-$platform-$arch" "kind-$platform-$arch"
fetch "https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-$platform-$arch.sha256sum" kind.sha256sum
# macOS supplies shasum; Linux supplies sha256sum.
if command -v sha256sum >/dev/null; then sha256sum --check kind.sha256sum; else shasum -a 256 --check kind.sha256sum; fi
fetch "https://dl.k8s.io/release/$version/bin/$platform/$arch/kubectl" kubectl
fetch "https://dl.k8s.io/release/$version/bin/$platform/$arch/kubectl.sha256" kubectl.sha256
expected=$(cat kubectl.sha256)
[[ "$expected" =~ ^[a-f0-9]{64}$ ]] || { echo "Invalid kubectl checksum" >&2; exit 1; }
printf '%s  kubectl\n' "$expected" > kubectl.sha256sum
if command -v sha256sum >/dev/null; then sha256sum --check kubectl.sha256sum; else shasum -a 256 --check kubectl.sha256sum; fi
chmod 755 "kind-$platform-$arch" kubectl
mv "kind-$platform-$arch" "$bin_dir/kind"
mv kubectl "$bin_dir/kubectl"
archive="helm-v3.19.0-$platform-$arch.tar.gz"
fetch "https://get.helm.sh/$archive" "$archive"
fetch "https://get.helm.sh/$archive.sha256sum" helm.sha256sum
if command -v sha256sum >/dev/null; then sha256sum --check helm.sha256sum; else shasum -a 256 --check helm.sha256sum; fi
tar -xzf "$archive" "$platform-$arch/helm"
chmod 755 "$platform-$arch/helm"
mv "$platform-$arch/helm" "$bin_dir/helm"
echo "Installed kind v0.33.0, kubectl $version and Helm v3.19.0 in $bin_dir"
