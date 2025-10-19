# Repository Guidelines

## Project Structure & Module Organization
- `src/` holds the Python data pipeline: `collectors/` handle Riot ingestion, `transformers/` enforce schemas, `storage/` manages Parquet/JSON, and `utils/` wraps config and rate limiting helpers.
- `backend/` hosts the FastAPI service (`backend/api/main.py`) plus routers/services for recommendation endpoints.
- `frontend/` contains the Next.js client; use `frontend/app/` for routes, `frontend/components/` for reusable UI, and `frontend/lib/` for shared logic.
- `ml_pipeline/` captures offline feature work and stored artifacts; `tests/` contains pytest suites and `data/` is populated at runtime.

## Build, Test, and Development Commands
- Bootstrap Python tooling with `pip install -r requirements.txt`; load a 10-match sample via `python quickstart.py`.
- Scale collection using `python run_collector.py --ranks GOLD PLATINUM --matches-per-rank 100`.
- Launch the API with `python start_api.py`.
- In `frontend/`, run `npm install`, then `npm run dev` for local work or `npm run build && npm run start` for production parity.
- Core verification flows: `pytest --cov=src` for backend/schema changes, `npm run lint`, and `npm run type-check` for the UI.

## Coding Style & Naming Conventions
- Python code targets PEP 8: 4-space indentation, snake_case functions, PascalCase classes (`MatchCollector`), and type hints; keep validation inside Pydantic models.
- Scope FastAPI routers under `backend/api/routers/` by feature and import shared schemas from `backend/api/schemas.py`.
- Frontend modules are TypeScript-first; name components in PascalCase, colocate hooks/utilities in `frontend/lib/`, and fix lint issues with `npm run lint -- --fix`.

## Testing Guidelines
- Pytest discovery follows `pytest.ini` (`tests/`, `test_*.py`, `Test*` classes); extend `tests/test_schema.py` when updating validation rules.
- Run `pytest --cov=src --cov=backend` before proposing changes and add module-specific suites for new services.
- Frontend relies on linting and types; introduce Jest/Playwright specs under `frontend/__tests__/` for interactive flows.

## Commit & Pull Request Guidelines
- Mirror the short, imperative commit tone already in history (`Add frontend scaffold`, `Fix collector retries`) and keep each commit focused.
- Provide PRs with a summary, affected paths (`src/collectors`, `frontend/app`, etc.), proof of tests, and linked issues or tasks.
- Update supporting docs (`README.md`, `SETUP_GUIDE.md`, this guide) whenever workflows, config, or API contracts shift.

## Security & Configuration Tips
- Store secrets in `.env` or `config/config.yaml`; never commit personal Riot API keys or logs like `backend/api.log`.
- Note non-default config overrides in PRs so others can reproduce results.
- Exclude generated artifacts under `data/raw/` or cached models from commits.
