#!/bin/bash
set -euo pipefail

workspace="$PWD/.runtime/lean-mathlib"
toolkit_lean="$PWD/.runtime/lean/bin"
revision="f0957a7575317490107578ebaee9efaf8e62a4ab"
if [[ ! -d "$workspace/.git" ]]; then
  git init -q "$workspace"
fi
if ! git -C "$workspace" rev-parse --verify -q HEAD >/dev/null; then
  git -C "$workspace" fetch --depth=1 https://github.com/leanprover-community/mathlib4.git "$revision"
  git -C "$workspace" checkout --detach FETCH_HEAD
fi
if [[ "$(git -C "$workspace" rev-parse HEAD)" != "$revision" ]]; then
  echo "Expected the pinned Mathlib revision in $workspace." >&2
  exit 1
fi
cd "$workspace"
if [[ ! -f ".lake/build/lib/Mathlib.olean" ]]; then
  export XDG_CACHE_HOME="$workspace/.cache"
  "$toolkit_lean/lake" build Cache.Main
  "$toolkit_lean/lake" env "$toolkit_lean/lean" --run Cache/Main.lean get
fi
printf 'import Mathlib\nexample (x : ℤ) : (x + 1)^2 = x^2 + 2*x + 1 := by ring\n' |
  "$toolkit_lean/lake" env "$toolkit_lean/lean" --stdin
"$toolkit_lean/lake" env /usr/bin/printenv LEAN_PATH > .lean-path
printf '%s\n' "$revision" > .verified
