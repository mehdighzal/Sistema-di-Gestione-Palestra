#!/usr/bin/env bash
set -euo pipefail

LOCAL_FORWARD_PORT="${LOCAL_FORWARD_PORT:-15432}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TUNNEL_PID_FILE="${PROJECT_DIR}/.tunnel_${LOCAL_FORWARD_PORT}.pid"

detect_os() {
  case "${OSTYPE:-}" in
    linux-gnu*)
      echo linux
      ;;
    darwin*)
      echo mac
      ;;
    msys*|cygwin*)
      echo windows
      ;;
    *)
      case "$(uname -s 2>/dev/null)" in
        Linux*)
          echo linux
          ;;
        Darwin*)
          echo mac
          ;;
        MINGW*|MSYS*|CYGWIN*)
          echo windows
          ;;
        *)
          echo unknown
          ;;
      esac
      ;;
  esac
}

OS="$(detect_os)"

pids_listening_on_port() {
  local port=$1
  case "${OS}" in
    windows)
      netstat -ano 2>/dev/null \
        | awk -v p=":${port}" '$1 == "TCP" && $2 ~ p && $4 == "LISTENING" { print $5 }' \
        | sort -u
      ;;
    linux|mac|unknown)
      if command -v ss >/dev/null 2>&1; then
        ss -lntp "( sport = :${port} )" 2>/dev/null \
          | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' \
          | sort -u
      fi
      ;;
  esac
}

echo "==> Detected OS: ${OS}"
echo "==> Stopping tunnel on port ${LOCAL_FORWARD_PORT} (if running)..."

PIDS="$(pids_listening_on_port "${LOCAL_FORWARD_PORT}" || true)"

if [[ -n "${PIDS}" ]]; then
  for pid in ${PIDS}; do
    if [[ -n "${pid}" ]] && [[ "${pid}" =~ ^[0-9]+$ ]]; then
      kill -9 "${pid}" 2>/dev/null || true
    fi
  done
  echo "==> Sent SIGKILL to PIDs: ${PIDS}"
else
  echo "==> No active listener found on ${LOCAL_FORWARD_PORT}."
fi

if [[ -f "${TUNNEL_PID_FILE}" ]]; then
  rm -f "${TUNNEL_PID_FILE}"
fi
