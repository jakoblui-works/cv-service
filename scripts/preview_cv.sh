#!/usr/bin/env sh
# Run scripts/preview_cv.py inside the cv-service image (the only place with TeX Live).
# app/ and scripts/ are mounted over the image's copies, so content, template and code changes
# show up without a rebuild. Rebuild only when dependencies change:
#     docker build -t cv-service:local .
set -eu

cd "$(dirname "$0")/.."
mkdir -p previews

docker run --rm \
  --env-file .env \
  -v "$PWD/app:/app/app:ro" \
  -v "$PWD/scripts:/app/scripts:ro" \
  -v "$PWD/previews:/app/previews" \
  cv-service:local \
  python -m scripts.preview_cv "$@"
