#!/usr/bin/env bash
set -euo pipefail
cd /opt/reading-notes-builder
exec 9>/var/lock/reading-notes/build.lock
flock -n 9 || exit 75
pnpm install --frozen-lockfile
python3 tools/project.py check
receipt=$(mktemp tmp/build-job.XXXXXX)
trap 'rm -f "$receipt"' EXIT
python3 tools/project.py build > "$receipt"
python3 deploy/scripts/queue-release.py "$receipt"
