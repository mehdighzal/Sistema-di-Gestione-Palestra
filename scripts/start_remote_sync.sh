#!/usr/bin/env bash
set -euo pipefail

# Sync mode: local app -> remote PostgreSQL via SSH tunnel.
# OS-specific: Linux uses `ss`; Windows (Git Bash / MSYS) uses `netstat`.
# Override with env vars if needed.
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-82.165.187.131}"
REMOTE_DB_HOST="${REMOTE_DB_HOST:-127.0.0.1}"
REMOTE_DB_PORT="${REMOTE_DB_PORT:-5432}"
LOCAL_FORWARD_PORT="${LOCAL_FORWARD_PORT:-15432}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
VENV_DIR="${PROJECT_DIR}/venv"
TUNNEL_PID_FILE="${PROJECT_DIR}/.tunnel_${LOCAL_FORWARD_PORT}.pid"

# linux | windows (Git Bash / MSYS / Cygwin) | mac | unknown
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

# Exit 0 if something is listening on 127.0.0.1:port (tunnel likely already up)
port_is_listening() {
  local port=$1
  case "${OS}" in
    windows)
      netstat -ano 2>/dev/null \
        | awk -v p=":${port}" '$1 == "TCP" && $2 ~ p && $4 == "LISTENING" { found=1 } END { exit(found ? 0 : 1) }'
      ;;
    linux|mac|unknown)
      if command -v ss >/dev/null 2>&1; then
        ss -lnt "( sport = :${port} )" 2>/dev/null | awk 'NR>1 {found=1} END {exit(found?0:1)}'
      elif (echo >/dev/tcp/127.0.0.1/"${port}") 2>/dev/null; then
        return 0
      else
        return 1
      fi
      ;;
  esac
}

listener_pid_best_effort() {
  local port=$1
  case "${OS}" in
    windows)
      netstat -ano 2>/dev/null \
        | awk -v p=":${port}" '$1 == "TCP" && $2 ~ p && $4 == "LISTENING" { print $5; exit }'
      ;;
    linux|mac|unknown)
      if command -v ss >/dev/null 2>&1; then
        ss -lntp "( sport = :${port} )" 2>/dev/null \
          | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' \
          | head -n1
      fi
      ;;
  esac
}

activate_venv() {
  case "${OS}" in
    windows)
      if [[ -f "${VENV_DIR}/Scripts/activate" ]]; then
        # shellcheck source=/dev/null
        source "${VENV_DIR}/Scripts/activate"
        return
      fi
      ;;
    linux|mac|unknown)
      if [[ -f "${VENV_DIR}/bin/activate" ]]; then
        # shellcheck source=/dev/null
        source "${VENV_DIR}/bin/activate"
        return
      fi
      # fallback: Windows-style venv on odd setups
      if [[ -f "${VENV_DIR}/Scripts/activate" ]]; then
        # shellcheck source=/dev/null
        source "${VENV_DIR}/Scripts/activate"
        return
      fi
      ;;
  esac
  echo "ERROR: no venv activate script in ${VENV_DIR}/Scripts or ${VENV_DIR}/bin"
  exit 1
}

echo "==> Project: ${PROJECT_DIR}"
echo "==> Detected OS: ${OS}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: .env not found at ${ENV_FILE}"
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "ERROR: venv not found at ${VENV_DIR}"
  exit 1
fi

if port_is_listening "${LOCAL_FORWARD_PORT}"; then
  echo "==> Port ${LOCAL_FORWARD_PORT} already listening (tunnel or service already up)."
else
  echo "==> Starting SSH tunnel ${LOCAL_FORWARD_PORT} -> ${REMOTE_DB_HOST}:${REMOTE_DB_PORT} (${REMOTE_USER}@${REMOTE_HOST})"
  if ! ssh -f -N \
    -L "${LOCAL_FORWARD_PORT}:${REMOTE_DB_HOST}:${REMOTE_DB_PORT}" \
    -o ExitOnForwardFailure=yes \
    "${REMOTE_USER}@${REMOTE_HOST}"; then
    echo ""
    echo "ERROR: SSH tunnel failed. If you see 'Address already in use':"
    echo "  - Stop the old tunnel: ./scripts/stop_remote_sync.sh"
    echo "  - Or use another port: LOCAL_FORWARD_PORT=15433 ./scripts/start_remote_sync.sh"
    echo "    (and set POSTGRES_PORT=15433 in .env for this session)"
    exit 1
  fi
fi

LISTENER_PID="$(listener_pid_best_effort "${LOCAL_FORWARD_PORT}" || true)"
if [[ -n "${LISTENER_PID}" ]]; then
  echo "${LISTENER_PID}" > "${TUNNEL_PID_FILE}"
  echo "==> Tunnel listener pid: ${LISTENER_PID}"
fi

echo "==> Activating virtualenv and validating DB connection..."
activate_venv
python manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('select 1'); print('DB OK:', c.fetchone()[0])"

echo "==> Starting Django server on 0.0.0.0:8000"
python manage.py runserver 0.0.0.0:8000
