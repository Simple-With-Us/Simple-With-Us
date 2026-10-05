#!/usr/bin/env bash
# Cursor cloud agent install script for Simple-With-Us.
#
# This repo is a static HTML/site catalog hosted on GitHub Pages.
# There is no Node toolchain, no package manager lockfile, and no
# build step.  The only build-time helper is scripts/build_catalog.py,
# which is plain Python 3 with no third-party dependencies.
#
# macOS / iOS / Xcode steps are intentionally skipped here:  Simple-With-Us
# itself is platform-agnostic static HTML.  macOS and iOS fleet app builds
# live in their own fleet repos (see AGENTS.md).
#
# Install disk state persists across Cursor agent starts, but exported
# shell variables do not.  Anything that must be in the environment for
# every boot belongs in cursor-cloud-start.sh, not here.
#
# Idempotent on Ubuntu Linux.  Safe to re-run.

set -euo pipefail

echo "[cursor-cloud-install] Simple-With-Us: verifying base tools"

# python3 drives scripts/build_catalog.py and the *_test_catalog*.py
# checks.  composer-latest already ships python3, but we still probe so
# the install fails loudly if the base image ever changes.
if ! command -v python3 >/dev/null 2>&1; then
  echo "[cursor-cloud-install] ERROR: python3 not found on PATH" >&2
  exit 1
fi

PY_VERSION="$(python3 --version 2>&1 || true)"
echo "[cursor-cloud-install] python3 available: ${PY_VERSION}"

# git is required for the agent's own workflow.  composer-latest ships
# git, but a quick probe keeps the install self-checking.
if ! command -v git >/dev/null 2>&1; then
  echo "[cursor-cloud-install] ERROR: git not found on PATH" >&2
  exit 1
fi

GIT_VERSION="$(git --version 2>&1 || true)"
echo "[cursor-cloud-install] git available: ${GIT_VERSION}"

# No node, no pnpm, no Xcode.  Static HTML only.
echo "[cursor-cloud-install] macOS / iOS / Xcode steps skipped (Linux-only host, static catalog)"
echo "[cursor-cloud-install] done"