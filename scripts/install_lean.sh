#!/bin/bash
set -euo pipefail

runtime=".runtime/lean"
archive=".runtime/lean-4.9.0-darwin_aarch64.tar.zst"
verify() {
  printf '%s  %s\n' 76a289d8a056e1ebd40cbb5590a1c393257673dab499777e0de32c08d7202585 "$1" | shasum -a 256 -c
}
if [[ ! -f "$archive" ]]; then
  stage=$(mktemp -d .runtime/.lean-download.XXXXXXXX)
  trap 'if [[ -f "$stage/archive.tar.zst" ]]; then unlink "$stage/archive.tar.zst"; fi; rmdir "$stage"' EXIT
  /usr/bin/curl -fsSL --retry 2 --max-time 900 \
    https://github.com/leanprover/lean4/releases/download/v4.9.0/lean-4.9.0-darwin_aarch64.tar.zst \
    -o "$stage/archive.tar.zst"
  verify "$stage/archive.tar.zst"
  mv "$stage/archive.tar.zst" "$archive"
  rmdir "$stage"
  trap - EXIT
fi
verify "$archive"
if [[ ! -x "$runtime/bin/lean" ]]; then
  stage=$(mktemp -d .runtime/.lean-unpack.XXXXXXXX)
  trap 'rm -rf -- "$stage"' EXIT
  tar xf "$archive" -C "$stage"
  "$stage/lean-4.9.0-darwin_aarch64/bin/lean" --version
  if [[ ! -e "$runtime" ]]; then
    mv "$stage/lean-4.9.0-darwin_aarch64" "$runtime"
  fi
fi
"$runtime/bin/lean" --version | grep -F 'commit 8f9843a4a5fe'
