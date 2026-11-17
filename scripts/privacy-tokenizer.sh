# tiktoken 0.14.0 indexes o200k_base by the SHA-1 of its upstream URL.
export TIKTOKEN_CACHE_DIR="$root/.runtime/models/privacy/tiktoken"

privacy_tokenizer_ready() {
  local encoding="$TIKTOKEN_CACHE_DIR/fb374d419588a4632f3f557e76b4b70aebbca790"
  [[ -f "$encoding" ]] &&
    printf '%s  %s\n' '446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d' "$encoding" |
      /usr/bin/shasum -a 256 -c --status
}
