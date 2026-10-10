#!/usr/bin/env bash
# Send a Python job to the Claude Fusion Bridge add-in in Fusion and print its result.
# Usage: fusion_run.sh <job.py> [timeout_seconds]
# The job is copied into the bridge inbox under a unique name; the script waits
# for the matching JSON in the outbox and prints it. Exit code 1 if the job failed.
set -euo pipefail

job_src="$1"
timeout="${2:-120}"
bridge="${USERPROFILE:-$HOME}/Documents/ClaudeFusion/bridge"
bridge="${bridge//\\//}"

if [ ! -f "$bridge/status.json" ]; then
  echo "Bridge not found at $bridge. Is Fusion running with the Claude Fusion Bridge add-in?" >&2
  exit 2
fi

name="$(basename "$job_src" .py)_$(date +%Y%m%d_%H%M%S)"
cp "$job_src" "$bridge/inbox/$name.tmp"
mv "$bridge/inbox/$name.tmp" "$bridge/inbox/$name.py"

out="$bridge/outbox/$name.json"
for ((i = 0; i < timeout * 2; i++)); do
  if [ -f "$out" ]; then
    py="${DUCCKY_PY:-$USERPROFILE/.venvs/duccky/Scripts/python.exe}"
    if [ -x "$py" ]; then
      "$py" -c 'import json,sys; d=json.load(open(sys.argv[1])); print("ok:", d["ok"], " seconds:", d["seconds"]); print(d["stdout"], end=""); print(d["error"] or "", end=""); [print("image:", i) for i in d["images"]]' "$out"
    else
      cat "$out"
    fi
    grep -q '"ok": true' "$out"
    exit $?
  fi
  sleep 0.5
done
echo "Timed out after ${timeout}s waiting for $out (a modal dialog in Fusion blocks jobs)" >&2
exit 3
