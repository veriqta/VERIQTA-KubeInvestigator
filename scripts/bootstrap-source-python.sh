#!/usr/bin/env bash
# Supported upstream CPython source build for macOS; never replace system Python.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ $(uname -s) == Darwin ]] || { echo 'This tested bootstrap is macOS-only; see installation.md for other hosts.' >&2; exit 2; }
command -v brew >/dev/null || { echo 'Install Homebrew from brew.sh first.' >&2; exit 2; }
xcrun --find clang >/dev/null
prefix=${1:-"$PWD/.local/python-3.12.16"}
[[ "$prefix" = /* && ! -e "$prefix" ]] || { echo 'Choose a new absolute installation prefix; existing paths are preserved.' >&2; exit 2; }
brew install sqlite openssl@3
sqlite_prefix=$(brew --prefix sqlite)
openssl_prefix=$(brew --prefix openssl@3)
umask 077
mkdir -p .capture
scratch=$(mktemp -d "$PWD/.capture/python-build.XXXXXX")
trap 'rm -rf "$scratch"' EXIT
curl --fail --silent --show-error --location --retry 2 --max-time 180 \
  https://www.python.org/ftp/python/3.12.16/Python-3.12.16.tar.xz -o "$scratch/python.tar.xz"
printf '%s  %s\n' b5796915dc45ff745cfb4e990a7e7c93d6f546328a102ce31448d69ebc37575c "$scratch/python.tar.xz" | shasum -a 256 --check
tar -xJf "$scratch/python.tar.xz" -C "$scratch"
cd "$scratch/Python-3.12.16"
LIBSQLITE3_CFLAGS="-I$sqlite_prefix/include" \
LIBSQLITE3_LIBS="-L$sqlite_prefix/lib -lsqlite3" \
./configure --prefix="$prefix" --with-ensurepip=install --with-system-expat=no \
  --with-openssl="$openssl_prefix" --with-openssl-rpath=auto
make -j2
make altinstall
"$prefix/bin/python3.12" -m pip install --upgrade --only-binary=:all: pip==26.2.2
"$prefix/bin/python3.12" - <<'PY'
import sqlite3, pyexpat, ssl, platform
assert sqlite3.sqlite_version_info >= (3, 54, 1), sqlite3.sqlite_version
assert tuple(map(int, pyexpat.EXPAT_VERSION.removeprefix('expat_').split('.'))) >= (2,9,0)
assert platform.mac_ver()[0], 'Unable to read macOS version'
assert ssl.create_default_context().cert_store_stats()['x509_ca'] > 0
print('Built maintained CPython; SQLite:',sqlite3.sqlite_version,'Expat:',pyexpat.EXPAT_VERSION)
PY
printf 'Use: make setup PYTHON=%s/bin/python3.12 VENV=.venv-source\n' "$prefix"
