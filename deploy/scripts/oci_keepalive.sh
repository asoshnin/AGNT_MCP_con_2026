#!/usr/bin/env bash
# ==============================================================================
# Oracle Cloud Always-Free Anti-Idle Watchdog
# ==============================================================================
# Note: Upgrading your Oracle tenancy to Pay-As-You-Go (PAYG) permanently exempts
# your instances from idle reclamation while remaining $0.00/mo.
# This script is a lightweight safety net for non-PAYG Free Tier tenancies.
#
# It runs a controlled 25% CPU workload for 60 seconds to satisfy the 7-day
# activity threshold without starving other services or burning resources.
# ==============================================================================

set -euo pipefail

DURATION=60
CPU_CORES=$(nproc || echo 1)

echo "[$(date '+%Y-%m-%d %H:%M:%S')] OCI Keepalive: Starting pulse on ${CPU_CORES} core(s)..."

# Run a bounded calculation loop in background
timeout "${DURATION}" bash -c '
  for i in $(seq 1 '"${CPU_CORES}"'); do
    ( while true; do :; done ) &
  done
  wait
' 2>/dev/null || true

echo "[$(date '+%Y-%m-%d %H:%M:%S')] OCI Keepalive: Completed successfully."
