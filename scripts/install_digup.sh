#!/bin/bash
set -euo pipefail
umask 077
root="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$root"
helper=".runtime/digup/digup"
models="$root/.runtime/models/digup"
mkdir -p "$(dirname "$helper")" "$models"

if [[ ! -x "$helper" ]]; then
  work="$(mktemp -d "$root/.runtime/digup-install.XXXXXXXX")"
  mount="$work/mount"
  mkdir "$mount"
  trap 'hdiutil detach "$mount" >/dev/null 2>&1 || true; [[ ! -f "$work/DigUp.dmg" ]] || unlink "$work/DigUp.dmg"; [[ ! -f "$work/digup" ]] || unlink "$work/digup"; rmdir "$mount" "$work" 2>/dev/null || true' EXIT
  curl --fail --location --retry 2 \
    'https://github.com/ARahim3/DigUp/releases/download/v0.6.2/DigUp-0.6.2.dmg' \
    --output "$work/DigUp.dmg"
  printf '%s  %s\n' '043033bdbe0c7c5fcb56545711c19d0ccf2cb9be58798d0e47f7c35e902cc5fd' "$work/DigUp.dmg" | shasum -a 256 -c
  hdiutil attach -readonly -nobrowse -mountpoint "$mount" "$work/DigUp.dmg" >/dev/null
  codesign --verify --deep --strict "$mount/DigUp.app"
  spctl --assess --type execute --verbose "$mount/DigUp.app"
  cp "$mount/DigUp.app/Contents/Helpers/digup" "$work/digup"
  codesign --verify --strict "$work/digup"
  mv -f "$work/digup" "$helper"
  hdiutil detach "$mount" >/dev/null
fi
printf '%s  %s\n' 'c333e259196b1a4426234716bcce0e2e1ada2660c6aba3be850074707ae3650b' "$helper" | shasum -a 256 -c

"$helper" download-model --to "$models" | awk '/"event":"progress"/ {next} {print; fflush()}'
(
  cd "$models"
  if [[ -f .verified ]]; then unlink .verified; fi
  shasum -a 256 -c <<'CHECKSUMS'
2188ac1deca4b77dffefd603c2776a9d76d9d74ec01841392982ebb840b09135  embeddinggemma-2-Q8_0.gguf
c4a8a52691ecef40618438928bdf9e68379b854e24166f292592353db0aab64f  mmproj-embeddinggemma-2-Q8_0.gguf
CHECKSUMS
  touch .verified
)
