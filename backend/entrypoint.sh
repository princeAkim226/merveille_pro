#!/usr/bin/env bash
set -euo pipefail

echo "[merveille] collectstatic…"
python manage.py collectstatic --no-input

echo "[merveille] migrate…"
python manage.py migrate --no-input

if [ "${RUN_SEED:-false}" = "true" ]; then
  echo "[merveille] seed_data…"
  python manage.py seed_data || true
fi

echo "[merveille] gunicorn on :${PORT:-8000}"
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_WORKERS:-2}" \
  --timeout 120
