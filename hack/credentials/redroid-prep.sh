#!/usr/bin/env bash
#
# Host preparation for ReDroid. ReDroid runs Android on the HOST kernel, so the
# binder (and on older kernels, ashmem) modules must be loaded before starting
# the container. Run on the host (not in a container):
#
#   sudo ./redroid-prep.sh
set -euo pipefail

echo "[redroid-prep] loading binder_linux"
if ! lsmod | grep -q '^binder_linux'; then
  modprobe binder_linux devices="binder,hwbinder,vndbinder" 2>/dev/null \
    || modprobe binder_linux 2>/dev/null \
    || echo "[redroid-prep] binder_linux not loadable as a module (may be built-in / binderfs)"
fi

echo "[redroid-prep] loading ashmem_linux (older kernels only)"
if ! modprobe ashmem_linux 2>/dev/null; then
  echo "[redroid-prep] ashmem_linux unavailable — that's expected on modern kernels."
  echo "[redroid-prep] The compose passes androidboot.use_memfd=true to avoid ashmem."
fi

echo "[redroid-prep] current state:"
lsmod | grep -E 'binder|ashmem' || echo "  (nothing in lsmod — likely built-in)"
ls -l /dev/binder* 2>/dev/null || true

echo "[redroid-prep] done"
