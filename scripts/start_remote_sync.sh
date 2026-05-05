#!/usr/bin/env bash
set -euo pipefail

# Sync mode: local app -> remote PostgreSQL via SSH tunnel.
# Override these with env vars if needed.
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-82.165.187.131}"
REMOTE_DB_HOST="${REMOTE_DB_HOST:-127.0.0.1}"
REMOTE_DB_PORT="${REMOTE_DB_PORT:-5432}"
LOCAL_FORWARD_PORT="${LOCAL_FORWARD_PORT:-15432}"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
VENV_DIR="${PROJECT_DIR}/venv"
TUNNEL_PID_FILE="${PROJECT_DIR}/.tunnel_15432.pid"

echo "==> Project: ${PROJECT_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: .env not found at ${ENV_FILE}"
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "ERROR: venv not found at ${VENV_DIR}"
  exit 1
fi

if ss -lnt "( sport = :${LOCAL_FORWARD_PORT} )" | awk 'NR>1 {found=1} END {exit(found?0:1)}'; then
  echo "==> Tunnel port ${LOCAL_FORWARD_PORT} already listening."
else
  echo "==> Starting SSH tunnel ${LOCAL_FORWARD_PORT} -> ${REMOTE_DB_HOST}:${REMOTE_DB_PORT} (${REMOTE_USER}@${REMOTE_HOST})"
  ssh -f -N \
    -L "${LOCAL_FORWARD_PORT}:${REMOTE_DB_HOST}:${REMOTE_DB_PORT}" \
    -o ExitOnForwardFailure=yes \
    "${REMOTE_USER}@${REMOTE_HOST}"
fi

# Record the listener PID when possible (best effort)
LISTENER_PID="$(
  ss -lntp "( sport = :${LOCAL_FORWARD_PORT} )" 2>/dev/null \
    | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' \
    | head -n1 \
    || true
)"
if [[ -n "${LISTENER_PID}" ]]; then
  echo "${LISTENER_PID}" > "${TUNNEL_PID_FILE}"
  echo "==> Tunnel listener pid: ${LISTENER_PID}"
fi

echo "==> Activating virtualenv and validating DB connection..."
source "${VENV_DIR}/bin/activate"
python manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('select 1'); print('DB OK:', c.fetchone()[0])"

echo "==> Starting Django server on 0.0.0.0:8000"
python manage.py runserver 0.0.0.0:8000
