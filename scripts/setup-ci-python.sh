#!/usr/bin/env bash
# Ubuntu 24.04 hosted images document preinstalled Homebrew, outside PATH.
# No installer download, loader override, system-library replacement or bypass.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ ${GITHUB_ACTIONS:-} == true && -n ${GITHUB_ENV:-} && -n ${GITHUB_PATH:-} ]] || {
  echo 'This helper is only for the prepared GitHub runner; see installation.md locally.' >&2; exit 2;
}
brew_bin=/home/linuxbrew/.linuxbrew/bin/brew
[[ -x "$brew_bin" ]] || { echo 'Expected supported Ubuntu runner Homebrew is unavailable' >&2; exit 2; }
brew_directory=$(dirname "$brew_bin")
export PATH="$brew_directory:$PATH"
"$brew_bin" install python@3.12 sqlite
python_prefix=$("$brew_bin" --prefix python@3.12)
"$python_prefix/bin/python3.12" src/kubeinvestigator/sqlite_runtime.py
printf 'PYTHON=%s\n' "$python_prefix/bin/python3.12" >> "$GITHUB_ENV"
printf '%s\n' "$python_prefix/libexec/bin" >> "$GITHUB_PATH"
