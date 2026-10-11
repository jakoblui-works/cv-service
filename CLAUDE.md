# cv-service

Taskiq worker that owns the whole CV domain: content, selection, LaTeX rendering, PDF compile + S3 cache, and the `cv` Postgres schema.

## Commands
```sh
uv sync
uv run ruff check && uv run mypy && uv run pytest
uv run alembic upgrade head
uv run taskiq worker app.core.broker:broker --fs-discover --tasks-pattern "app/**/tasks.py"
docker build -t cv-service:local .     # TeX Live lives only in the image
scripts/preview_cv.sh [args]           # render previews/ inside the image (app/ and scripts/ are mounted)
uv run python -m scripts.smoke_check   # compile every title (needs TeX, so run it in the image)
uv run python -m scripts.send_generate # send a cv.generate.v1 task to a running worker
```
Tests need Postgres (CI: a `postgres:18` service; locally, the api repo's `compose.dev.yml` stack).

## Layout
- `app/content/`: CV content data, loader, models; `selection/` (the `SelectionRequest` pipeline).
- `app/render/`: Jinja LaTeX templates, escaping, `compile.py`.
- `app/pdfs/`: PDF cache (S3 key = sha256(LaTeX source).pdf).
- `app/options/`: builds and publishes `cv.published_options`.
- `app/generate/`, `app/health/`: Taskiq tasks. Entry points always live in `app/**/tasks.py`.
- `app/core/`: settings, broker, database. `app/storage/`: S3.

## Contracts
- **Owns** the `cv` schema. `cv.published_options` v1 is upserted on worker startup; the api reads it. A new shape means a new version row; never change v1 in place.
- **Handles** `cv.generate.v1`: `generate(request: dict, session) -> "<digest>.pdf"`. The request fields are `SelectionRequest` (`title_id`, `concept_ids`, `skill_ids`); the api mirrors them.

## Gotchas
- Contact details (`CONTACT__*`) are `SecretStr`, injected at runtime, and must never be logged, committed, or put in test fixtures. LaTeX compiler output can contain them too.
- `cv.tex` and `previews/` contain real contact details and are git-ignored. Keep it that way.
- mypy is strict and covers `app`, `tests`, `migrations`, `scripts`.
