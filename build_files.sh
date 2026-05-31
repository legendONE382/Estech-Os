#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail

python -m pip install -r requirements.txt
python manage.py collectstatic --no-input || true

if [[ -n "${DATABASE_URL:-}" ]] || [[ -n "${POSTGRES_URL:-}" ]]; then
  python manage.py migrate --noinput
else
  echo "Skipping Django migrations because DATABASE_URL or POSTGRES_URL is not configured."
fi
