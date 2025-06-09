#!/usr/bin/env sh
set -e
python manage.py makemigrations
python manage.py migrate --no-input
python manage.py search_index --rebuild -f --parallel --refresh
# exec uvicorn manthrabin_backend.asgi:application --host 0.0.0.0 --port 8000 "$@"
exec python manage.py runserver 0.0.0.0:8000
