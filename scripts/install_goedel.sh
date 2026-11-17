#!/bin/bash
set -euo pipefail

model_dir=".runtime/models/goedel"
repo="mradermacher/Goedel-Prover-V2-8B-GGUF"
revision="43fab68ec71738a75b0a84738e18b222d2d4e249"
name="Goedel-Prover-V2-8B.Q4_K_M.gguf"
digest="919203ed088d6260fbbe124688ca04cb3e213cf63a9ed35346c69e4bec914c02"
mkdir -p "$model_dir"
rm -f "$model_dir/.verified"
if [[ ! -f "$model_dir/$name" ]]; then
  partial="$model_dir/$name.partial"
  curl -fsSL --retry 3 --continue-at - "https://huggingface.co/$repo/resolve/$revision/$name" -o "$partial"
  printf '%s  %s\n' "$digest" "$partial" | shasum -a 256 -c
  mv -f "$partial" "$model_dir/$name"
fi
printf '%s  %s\n' "$digest" "$model_dir/$name" | shasum -a 256 -c
marker=$(mktemp "$model_dir/.verify.XXXXXXXX")
trap 'rm -f "$marker"' EXIT
printf '%s@%s\n' "$repo" "$revision" > "$marker"
mv -f "$marker" "$model_dir/.verified"
