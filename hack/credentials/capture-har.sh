#!/usr/bin/env bash
#
# Reverse-proxy capture: route the CatGenie app's traffic through mitmproxy and
# dump every flow to a HAR file. Runs entirely inside the tools container.
#
# Pipeline:
#   1. mitmdump listens on 0.0.0.0:8080 and writes out/catgenie.har (hardump).
#   2. The device's global HTTP proxy is pointed at the tools container IP.
#   3. The app is spawned under frida/ssl-unpin.js so cert pinning / TLS
#      validation is bypassed and mitmproxy can read the HTTPS bodies.
#
# Then drive the app (log in, open the device, press Clean…) — every request and
# response is recorded. Ctrl-C (or the timeout) tears it all down and restores
# the device proxy.
#
#   capture-har.sh [seconds]      # default 600
set -euo pipefail

PKG="${PKG:-com.petnovations}"
PROXY_PORT="${PROXY_PORT:-8080}"
DURATION="${1:-600}"
HAR="out/catgenie.har"

mkdir -p out
adb connect "${EMULATOR_HOST}:5555" >/dev/null 2>&1 || true
adb wait-for-device

# This container's IP on the compose network — the address the device dials.
TOOLS_IP="$(hostname -i | awk '{print $1}')"
echo "[har] tools proxy: ${TOOLS_IP}:${PROXY_PORT}  ->  ${HAR}"

cleanup() {
  echo "[har] tearing down"
  adb shell settings delete global http_proxy >/dev/null 2>&1 || true
  adb shell settings put global http_proxy :0 >/dev/null 2>&1 || true
  kill "${MITM_PID:-0}" "${FRIDA_PID:-0}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# 1. mitmproxy with HAR export (built-in `hardump` addon).
mitmdump --listen-host 0.0.0.0 --listen-port "${PROXY_PORT}" \
  --set hardump="${HAR}" --set termlog_verbosity=warn --showhost \
  > out/mitmdump.log 2>&1 &
MITM_PID=$!
sleep 3

# 2. Point the device at the proxy.
adb shell settings put global http_proxy "${TOOLS_IP}:${PROXY_PORT}"
echo "[har] device proxy set"

# 3. Spawn the app with TLS unpinning so mitmproxy can decrypt.
adb shell am force-stop "${PKG}" || true
frida -H 127.0.0.1:27042 -f "${PKG}" -l frida/ssl-unpin.js > out/ssl-unpin.log 2>&1 &
FRIDA_PID=$!

echo "[har] CAPTURING for ${DURATION}s — drive the app now (log in / open device)."
echo "[har]   mitmdump log: out/mitmdump.log   |   har: ${HAR}"
sleep "${DURATION}"
echo "[har] done"
