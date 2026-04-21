#!/usr/bin/env bash
set -euo pipefail

REF_ROOT="${1:-/Users/weiyi/_external/recovercot_refs}"
mkdir -p "$REF_ROOT"

clone_or_update() {
  local name="$1"
  local url="$2"
  if [[ -d "$REF_ROOT/$name/.git" ]]; then
    echo "Updating $name"
    git -C "$REF_ROOT/$name" pull --ff-only
  else
    echo "Cloning $name"
    git clone --depth 1 "$url" "$REF_ROOT/$name"
  fi
}

clone_or_update webarena https://github.com/ServiceNow/webarena
clone_or_update webarena-verified https://github.com/ServiceNow/webarena-verified
clone_or_update Mind2Web https://github.com/OSU-NLP-Group/Mind2Web
clone_or_update WebVoyager https://github.com/MinorJerry/WebVoyager
