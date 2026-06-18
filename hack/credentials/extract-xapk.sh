#!/usr/bin/env bash
#
# Extract the split APKs from an .xapk/.apkm bundle into ./apk so they can be
# installed with `adb install-multiple` (no re-signing needed — the splits keep
# their original developer signature).
#
#   ./extract-xapk.sh catgenie.xapk
set -euo pipefail

SRC="${1:?usage: extract-xapk.sh <file.xapk>}"
OUT="apk"

rm -rf "${OUT}"
mkdir -p "${OUT}"

# -j flattens paths, '*.apk' grabs base + config splits and skips icon/manifest.
unzip -o -j "${SRC}" '*.apk' -d "${OUT}" >/dev/null

# Normalize the base apk name (ApkPure names it after the package).
if [ ! -f "${OUT}/base.apk" ]; then
  base="$(ls "${OUT}" | grep -vE '^config\.' | grep -E '\.apk$' | head -1)"
  [ -n "${base}" ] && mv "${OUT}/${base}" "${OUT}/base.apk"
fi

echo "Extracted to ${OUT}/:"
ls -1 "${OUT}"

echo
echo "Native ABI splits present:"
ls -1 "${OUT}" | grep -E 'config\.(arm64_v8a|armeabi_v7a|x86|x86_64)\.apk' || echo "  (none)"
