#!/bin/bash
set -e
cd Manthrabin_backend
docker compose --profile=production up --build -d
docker compose --profile=production up frontend -d
