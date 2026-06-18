#!/usr/bin/env bash
#
# Connect to the emulator over adb, then download + push + start a frida-server
# whose version matches the installed frida-tools. Runs inside the `tools`
# container.
set -euo pipefail

EMULATOR_HOST="${EMULATOR_HOST:-emulator}"
FRIDA_ARCH="${FRIDA_ARCH:-x86_64}"

echo "[setup-frida] connecting to ${EMULATOR_HOST}:5555"
adb connect "${EMULATOR_HOST}:5555" >/dev/null
adb wait-for-device

echo "[setup-frida] gaining root (Google-APIs image is rootable)"
adb root >/dev/null 2>&1 || true
sleep 2
adb connect "${EMULATOR_HOST}:5555" >/dev/null 2>&1 || true
adb wait-for-device

FRIDA_VERSION="$(frida --version)"
SERVER="frida-server-${FRIDA_VERSION}-android-${FRIDA_ARCH}"
URL="https://github.com/frida/frida/releases/download/${FRIDA_VERSION}/${SERVER}.xz"

if [ ! -f "/tmp/${SERVER}" ]; then
  echo "[setup-frida] downloading ${SERVER} (frida ${FRIDA_VERSION})"
  curl -fsSL "${URL}" | unxz > "/tmp/${SERVER}"
fi

echo "[setup-frida] pushing frida-server"
adb push "/tmp/${SERVER}" /data/local/tmp/frida-server >/dev/null
adb shell chmod 755 /data/local/tmp/frida-server

echo "[setup-frida] (re)starting frida-server"
adb shell "pkill frida-server || true"
adb shell "nohup /data/local/tmp/frida-server >/dev/null 2>&1 &"
sleep 2

echo "[setup-frida] forwarding frida port 27042"
adb forward tcp:27042 tcp:27042 >/dev/null

echo "[setup-frida] ready. Devices:"
frida-ps -H 127.0.0.1:27042 >/dev/null && echo "[setup-frida] frida connected OK"
