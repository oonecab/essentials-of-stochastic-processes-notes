#!/usr/bin/env bash
# Linux uses util-linux flock. macOS dry-runs use the same kernel flock via Python.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root=/srv/reading-notes
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
    if [[ "${args[$i]}" == --root ]]; then
        i=$((i+1)); root="${args[$i]:?--root needs a directory}"
    fi
done
[[ -d "$root" && ! -L "$root" && ! -L "$root/.publish.lock" ]] || { echo 'A real, prepared deployment root is required' >&2; exit 2; }
if command -v flock >/dev/null 2>&1; then
    exec 9>"$root/.publish.lock"
    flock -n 9 || { echo 'Another publish holds the lock' >&2; exit 75; }
    exec python3 "$here/publish_release.py" --lock-fd 9 "${args[@]}"
fi
exec python3 "$here/publish_release.py" "${args[@]}"
