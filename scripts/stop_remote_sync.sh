#!/usr/bin/env bash
set -euo pipefail

LOCAL_FORWARD_PORT="${LOCAL_FORWARD_PORT:-15432}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TUNNEL_PID_FILE="${PROJECT_DIR}/.tunnel_15432.pid"

echo "==> Stopping tunnel on port ${LOCAL_FORWARD_PORT} (if running)..."

PIDS="$(
  ss -lntp "( sport = :${LOCAL_FORWARD_PORT} )" 2>/dev/null \
    | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' \
    | sort -u \
    || true
)"
if [[ -n "${PIDS}" ]]; then
  # shellcheck disable=SC2086
  kill -9 ${PIDS} || true
  echo "==> Killed PIDs: ${PIDS}"
else
  echo "==> No active listener found on ${LOCAL_FORWARD_PORT}."
fi

if [[ -f "${TUNNEL_PID_FILE}" ]]; then
  rm -f "${TUNNEL_PID_FILE}"
fi
