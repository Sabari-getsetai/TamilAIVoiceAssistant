# Repository Guidelines

## Project Structure & Module Organization
Core backend logic lives in `backend/` (FastAPI routers under `backend/api`, RAG components under `backend/rag`, infra helpers in `backend/infrastructure`). The Next.js dashboard is under `app/nextjs/` with Material UI views and React Query hooks. Database assets such as Alembic migrations sit in `migrations/`, while sample datasets and embeddings live inside `data/`. Tests are split between the root `test_*.py` sanity scripts and the more comprehensive `tests/` package. Reusable entrypoints and provisioning helpers live in `scripts/`, and all developer-facing docs stay under `docs/`.

## Build, Test, and Development Commands
- `./scripts/dev/dev-start.sh` — one-step bootstrap that provisions Docker services plus the backend API for local use.
- `docker compose -f docker-compose.dev.yml up -d` — runs PostgreSQL, Redis, MinIO, and Ollama locally; keep it running before touching FastAPI tests.
- `source .venv/bin/activate && uvicorn backend.main:app --reload` — lightweight backend loop when you prefer a native Python env.
- `cd app/nextjs && npm run dev` — launches the admin SPA at http://localhost:3000.
- `pytest tests test_admin_seeding.py --maxfail=1` — executes both suite directories; add `--cov=backend` for coverage tracking.
- `cd app/nextjs && npm run lint` — applies the `eslint-config-next` rules used in CI.

## Coding Style & Naming Conventions
Use 4-space indentation and type hints throughout Python modules, mirroring the existing FastAPI routers. Format Python with `black` (79-character target, as referenced in `alembic.ini`) and ensure Pydantic models stay in `snake_case`. React components and TypeScript files use PascalCase for components (e.g., `AdminDashboard.tsx`) and camelCase for hooks/utilities. Favor descriptive folder-level barrels over deeply nested imports, and keep localization-ready Tamil copy in dedicated constants rather than inline strings.

## Testing Guidelines
`pytest`, `pytest-asyncio`, and `httpx` power the API test suite, so place new async route checks in `tests/api/` and decorate with `@pytest.mark.asyncio`. Name modules `test_<feature>.py` and co-locate fixtures with the functionality they validate (e.g., embeddings fixtures inside `tests/rag/`). Always run `pytest --cov=backend --cov-report=term-missing` before opening a PR; document-only changes can rely on targeted smoke scripts like `test_api_response.py`. Align test data with Docker-provisioned services so IDs match seeded organizations.

## Commit & Pull Request Guidelines
Recent history (`Document flow fix`, `Add comprehensive test runner…`) shows short, imperative subjects; keep summaries under ~60 characters and focus on the behavior being changed. Reference related issues in the body (`Fixes #123`), describe schema or API changes explicitly, and include screenshots for UI adjustments in `app/nextjs`. Every PR should list the commands you ran (tests, lint, dev-start) plus any follow-up tasks. Request review from both backend and frontend owners when touching shared contracts such as auth payloads.

## Environment & Security Tips
Secrets and credentials belong in `.env` files or the ignored `credentials/` directory; never commit access tokens, model weights, or generated voice assets. When adding new services, update `docker-compose.dev.yml` alongside `README.md` so the stack remains reproducible. Keep large checkpoints in `models/` (already ignored) and prefer referencing them through environment variables defined in `backend/settings.py`.
