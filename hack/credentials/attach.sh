#!/usr/bin/env bash
#
# Like extract.sh, but ATTACHES to the already-running app instead of
# spawning (force-killing) it.  Use this when the app already has credentials
# loaded and you want to capture the refresh flow without resetting state.
#
#   attach.sh <script.js> [script2.js ...]
set -euo pipefail

[ "$#" -ge 1 ] || { echo "usage: attach.sh <frida-script.js> [more.js ...]"; exit 1; }

PKG="${PKG:-com.petnovations}"

LFLAGS=()
NAMES=()
for s in "$@"; do
  [ -f "${s}" ] || { echo "script not found: ${s}" >&2; exit 1; }
  LFLAGS+=( -l "${s}" )
  NAMES+=( "$(basename "${s}" .js)" )
done

mkdir -p out
LOG="out/attach-$(IFS=+; echo "${NAMES[*]}").log"

adb connect "${EMULATOR_HOST:-redroid}:5555" >/dev/null 2>&1 || true
adb wait-for-device

# Launch the app via am start if it isn't already running (no force-kill, no state wipe).
if ! adb shell pidof "${PKG}" >/dev/null 2>&1; then
  echo "[attach] app not running — launching via am start (state preserved)"
  adb shell monkey -p "${PKG}" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1 || \
    adb shell am start "$(adb shell cmd package resolve-activity --brief "${PKG}" 2>/dev/null | tail -1)" >/dev/null 2>&1
  sleep 2
fi

echo "[attach] attaching to ${PKG} with: ${NAMES[*]}"
echo "[attach] Ctrl-C to stop; output tee'd to ${LOG}"

# Resolve PID — more reliable than -n/-N across Frida versions
PID="$(adb shell pidof "${PKG}" 2>/dev/null | tr -d '\r')"
if [ -z "${PID}" ]; then
  echo "[attach] ERROR: ${PKG} is not running" >&2
  exit 1
fi
echo "[attach] found ${PKG} at PID ${PID}"

exec frida -H 127.0.0.1:27042 \
  -p "${PID}" \
  "${LFLAGS[@]}" \
  2>&1 | tee "${LOG}"
