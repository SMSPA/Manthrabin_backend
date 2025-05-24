#!/usr/bin/env sh
set -e
python manage.py migrate --no-input
exec uvicorn manthrabin_backend.asgi:application "$@"
