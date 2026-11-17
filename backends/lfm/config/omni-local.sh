export LFM_OMNI_SOCKET="${LFM_OMNI_SOCKET:-$HOME/Library/Application Support/Omni/omni.sock}"
if [[ "$LFM_OMNI_SOCKET" != /* || ! -S "$LFM_OMNI_SOCKET" ]]; then
  echo "Start Omni and wait for its local Unix socket before using --with-omni." >&2
  exit 1
fi
export OMNI_SOCKET="$LFM_OMNI_SOCKET"
export LFM_OMNI_ALLOWED_SOCKET="$LFM_OMNI_SOCKET"
