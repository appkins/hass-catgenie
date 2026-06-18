#!/usr/bin/env bash
#
# Spawn the app under one or more frida scripts via the remote frida-server,
# in a SINGLE session. Loading several scripts at once means one app launch /
# one login captures everything (key + token), instead of separate spawns that
# each kill the previous app instance.
#
#   extract.sh <script.js> [script2.js ...]
set -euo pipefail

[ "$#" -ge 1 ] || { echo "usage: extract.sh <frida-script.js> [more.js ...]"; exit 1; }

PKG="${PKG:-com.petnovations}"

LFLAGS=()
NAMES=()
for s in "$@"; do
  [ -f "${s}" ] || { echo "script not found: ${s}" >&2; exit 1; }
  LFLAGS+=( -l "${s}" )
  NAMES+=( "$(basename "${s}" .js)" )
done

mkdir -p out
LOG="out/$(IFS=+; echo "${NAMES[*]}").log"

echo "[extract] spawning ${PKG} with: ${NAMES[*]}"
echo "[extract] interact with the app (log in / open device / press Clean) to trigger the hooks"
echo "[extract] Ctrl-C to stop; output tee'd to ${LOG}"

exec frida -H 127.0.0.1:27042 \
  -f "${PKG}" \
  "${LFLAGS[@]}" \
  2>&1 | tee "${LOG}"
