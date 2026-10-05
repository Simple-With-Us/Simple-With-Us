#!/usr/bin/env bash
# Cursor cloud agent start script for Simple-With-Us.
#
# Simple-With-Us is a static HTML catalog with no secrets and no
# Infisical project (see the fleet brief).  There is nothing to fetch
# from a secret store and nothing to export into the environment.
#
# This script exists so the environment.json contract is satisfied and
# so an agent that lands here gets a one-line confirmation that the
# no-secrets posture is intentional.  It must always exit 0; a missing
# or unset dashboard secret MUST NOT fail the agent boot.
#
# Exported shell variables do NOT persist across Cursor agent starts,
# so anything that ever needs to live in the env would belong here, not
# in cursor-cloud-install.sh.

set -euo pipefail

REPO_NAME="Simple-With-Us"

# If, in the future, Simple-With-Us ever needs dashboard-injected
# secrets, the Cursor dashboard secrets would be added here.  Today
# the repo intentionally has none, so we just note that and return.

if [ -n "${INFISICAL_CLIENT_ID:-}" ] || [ -n "${INFISICAL_CLIENT_SECRET:-}" ]; then
  echo "[cursor-cloud-start] ${REPO_NAME}: dashboard secrets present but no Infisical project is configured for this repo; ignoring"
else
  echo "[cursor-cloud-start] ${REPO_NAME}: no secrets required (static HTML catalog)"
fi

exit 0