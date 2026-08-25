# Bitácora: MauriDev Harness adoption in Api_monolith

> Chronological record of the standard's adoption. Feeds `harness sync --check`
> and the harness Issue #3.

## Metadata

| Field | Value |
|-------|-------|
| Repo | MauriDev94/Api_monolith |
| Standard | MauriDev Harness (`uv` + `ruff` + `mypy` strict + `pytest` + `.harness/verify.toml` + CI workflow + pre-commit) |
| Started | 2026-08-21 |
| Closed | 2026-08-25 (this PR's CI green) |
| Tracking issues | #109 (closed), #112 (open) |
| Pull requests | #111 (adoption), #113 (mypy strict — this work) |
| Files touched (cumulative) | 13 (`pyproject.toml`, `.pre-commit-config.yaml`, 9 in `app/core/`, 1 in `app/`, 1 in `.harness/`) |
| Lines changed (cumulative) | +134 / -56 |

## Timeline

| Date | Event | Outcome |
|------|-------|---------|
| 2026-08-20 | Issue #109 opened: "Aplicar el estándar del harness a este repo" | Plan for adoption |
| 2026-08-21 | PR #110 opened (later closed without merge, replaced by #111) | First attempt |
| 2026-08-21 | PR #111 opened: `chore(harness): aplicar el estandar del MauriDev Harness` | Refined approach |
| 2026-08-23 | PR #111 merged into `main` (commit `5b212c5`) | Harness adopted |
| 2026-08-24 | Issue #112 opened: "task: habilitar mypy strict y arreglar los 42 type errors" | Strict mode follow-up |
| 2026-08-24 | Baseline measurement: `uv run mypy app --follow-imports=silent --no-incremental` → **42 errors in 12 files** | Confirmed pre-strict status |
| 2026-08-25 | Branch `chore/mypy-strict-fixes` created from `main` | Work isolated |
| 2026-08-25 | Per-file analysis of the 12 files: every fix is mechanical, no refactor of logic required | Strategy confirmed: in-line fixes, no new overrides |
| 2026-08-25 | Applied fixes in 5 working blocks, verified after each | 38 → 14 → 0 errors progressively |
| 2026-08-25 | Stop for user review of the 14 exception-handler signatures in `error_handling.py` | User approved `JSONResponse` as return type |
| 2026-08-25 | `mypy app` returns 0 errors with strict + warn_unreachable. Harness `--when push` exit 0 | Local gate green |
| 2026-08-25 | Pre-commit hook `mirrors-mypy` produced 29 false positives (isolated venv lacks FastAPI/Starlette/loguru stubs) | User chose option D: remove the hook |
| 2026-08-25 | Commit `b56886a`: `chore(types): enable mypy strict and fix 42 type errors` (+114/-46, 11 files) | Pushed |
| 2026-08-25 | PR #113 opened against `main` | Review-ready |
| 2026-08-25 | CI workflow run #32819412857: `quality` 30s pass + `tests` 50s pass | PR green |

## Phase 1: Harness adoption (#111)

What landed in `pyproject.toml`:

- `requires-python = ">=3.12"`
- Dependencies pinned (FastAPI 0.136.0, SQLAlchemy ≥2.0.49, pydantic-settings 2.13.1, psycopg2-binary 2.9.11, argon2-cffi 25.1.0, PyJWT 2.12.1, alembic 1.18.4, loguru 0.7.3, httpx 0.28.1)
- `[dependency-groups]` with `dev = [pytest, pytest-cov, pytest-sugar, ruff, mypy, pre-commit, testcontainers[postgres]]`
- `[tool.uv] default-groups = ["dev"]`
- `[tool.ruff]` with line-length 100, target-version py312, and `select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]`
- `[tool.ruff.lint.per-file-ignores]` exception for alembic `env.py` (E402 expected)
- `[tool.mypy] python_version = "3.12"`, `explicit_package_bases = true`, `ignore_missing_imports = true`
- Two initial mypy overrides (preserved through this PR):
  - `module = "app.core.exceptions.error_handling" disable_error_code = ["arg-type"]` (Starlette's narrow signature)
  - `module = "app.core.data.source.local.alembic.env" ignore_errors = true` (generated boilerplate)
- `[tool.coverage.run]` branch coverage, `[tool.coverage.report] fail_under = 85`
- `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `addopts = "--strict-markers"`, and explicit markers

What landed in `.harness/`:

- `verify.toml` declaring six gates (format, lint, types, tests, tests-full, hooks), each with measured `when` to minimise friction
- `verify.py` (existed before, unchanged)

What landed in `.github/workflows/`:

- `tests.yml` with two jobs: `quality` (lint + types + unit) and `tests` (full suite + coverage, requires `CI_DB_PASSWORD` + `CI_JWT_SECRET_KEY` secrets)

What landed in `.pre-commit-config.yaml`:

- `pre-commit-hooks` (v6.0.0): `check-merge-conflict`, `end-of-file-fixer`, `trailing-whitespace`
- `ruff-pre-commit` (v0.15.11): `ruff --fix` + `ruff-format`
- `mirrors-mypy` (v1.16.0): `mypy` with `args: [--ignore-missing-imports]` and `additional_dependencies: [pydantic-settings>=2.0, sqlalchemy>=2.0]`

What was **deliberately excluded from #111**: `mypy strict = true`. The plan split strict activation into a follow-up because adopting the standard and fixing pre-existing type errors are conceptually distinct changes. **Issue #112** tracked the follow-up.

## Phase 2: mypy strict + 42 fixes (#113 — this PR)

### Baseline measurement (pre-fix)

`uv run mypy app --no-incremental --follow-imports=silent` against `pyproject.toml` with `strict = true` and `warn_unreachable = true`:

```
Found 42 errors in 12 files (checked 120 source files)
```

Distribution by error code:

| Error code | Count | Files |
|------------|------:|-------|
| `no-untyped-def` | 32 | `app/core/exceptions/error_handling.py` (13), `app/main.py` (4), `app/core/data/source/local/database.py` (3), `app/core/middleware/{body_size_limit,rate_limit_global}.py` (5), `app/core/middleware/{security_headers,request_context}.py` (2), `app/core/data/source/local/sql_alchemy_base.py` ripple (4 via `misc`), `app/core/config/logger_config.py` (1), `app/core/exceptions/error_handling.py:180` (1) |
| `misc` | 4 | `app/features/{users,todos,auth}/infrastructure/models/*.py` × 1 each (Class cannot subclass SqlAlchemyBase (has type Any)) |
| `no-any-return` | 3 | `app/core/middleware/{body_size_limit,rate_limit_global}.py` |
| `no-untyped-call` | 2 | `app/core/data/source/local/database.py`, `app/main.py` |
| `attr-defined` | 1 | `app/core/data/source/local/database.py` (DBAPIConnection import path) |

### Fix strategy

The user's plan (issue #112) was a mix:

> PR inicial: selective `[[tool.mypy.overrides]]` by problematic file + easy fixes
> que se pueden hacer en el mismo PR sin riesgo

The fine-grained analysis (read every file before applying) showed that **all 42 errors are mechanical in-line fixes**, no refactor of logic. No new overrides were needed. Both existing overrides (alembic/env, exceptions/error_handling arg-type) cover different error codes and were preserved unchanged.

### Per-file fixes

| File | Lines | Type of change |
|------|------:|----------------|
| `pyproject.toml` | +2 | Add `strict = true`, `warn_unreachable = true` |
| `app/core/data/source/local/sql_alchemy_base.py` | +9/-3 | Replace `SqlAlchemyBase = declarative_base()` with `class SqlAlchemyBase(DeclarativeBase)` (SQLAlchemy 2.0 idiom). **Result**: 4 `misc` errors in ORM models disappeared without touching them. |
| `app/core/data/source/local/database.py` | +15/-7 | (a) Move `DBAPIConnection` import from `sqlalchemy.engine.events` to `sqlalchemy.engine.interfaces` (SQLAlchemy 2.0 relocation). (b) Type `_setup_slow_query_logging() -> None`. (c) Add documented `# type: ignore[no-untyped-def]` on the SQLAlchemy event callbacks (`before_execute`, `after_execute`) — their argument types depend on dialect/driver and cannot be statically resolved. |
| `app/core/middleware/body_size_limit.py` | +5/-2 | Type `__init__(self, app: ASGIApp, ...)` and `dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response`. |
| `app/core/middleware/rate_limit_global.py` | +5/-2 | Same pattern as `body_size_limit.py`. |
| `app/core/middleware/security_headers.py` | +3/-1 | Add `call_next: RequestResponseEndpoint` and `-> Response`. |
| `app/core/middleware/request_context.py` | +3/-3 | Same as `security_headers.py`. |
| `app/main.py` | +11/-3 | `lifespan` → `AsyncIterator[None]`, `custom_openapi` → `dict[str, Any]`, `read_root` → `dict[str, str]`, `health_check` → `Response`. Armonise `health_check` to return `JSONResponse` consistently (the 503 branch already did; the 200 branch returned `dict`). Drop the now-unused `# type: ignore[method-assign]` on `app.openapi = custom_openapi`. |
| `app/core/config/logger_config.py` | +8/-2 | Type `setup_logger() -> Logger` via `if TYPE_CHECKING: from loguru import Logger` (loguru's runtime Cython class is not re-exported but the `.pyi` declares the type at the top-level). |
| `app/core/exceptions/error_handling.py` | +27/-14 | Add `-> JSONResponse` to 12 exception handlers (matching what their bodies already construct) and `-> None` to `register_exception_handlers`. Add the same `TYPE_CHECKING` import pattern for the `_request_logger` helper's return type. |
| `.pre-commit-config.yaml` | +19/-3 | Remove the `mirrors-mypy` hook entirely (see Lessons Learned). |

### Mid-flight escape triggers (documented, none fired)

The issue #112 plan documented three mid-flight triggers that would force splitting the work into sub-issues:

1. **Trigger #1**: `SqlAlchemyBase: DeclarativeBase` surfacing new errors in the four ORM models (>3). **Did not fire.** The 4 `misc` errors disappeared and no new errors appeared — the ORM models were already in 2.0 idiom (`Mapped[T]` + `mapped_column()`).
2. **Trigger #2**: `attr-defined` for `DBAPIConnection` requiring more than 2 lines of investigation. **Did not fire.** Single-line import-path change.
3. **Trigger #3**: PR diff exceeding 150 lines. **Did not fire.** Final diff was +114/-46 across 11 files.

### Verification matrix

| Stage | Command | Result |
|-------|---------|--------|
| Block 1 (pyproject) | `uv run mypy app` | 42 errors (baseline confirmed) |
| Block 2 (sql_alchemy_base) | `uv run mypy app` | 38 errors (4 misc gone) |
| Block 3 (database.py) | `uv run mypy app` | 31 errors (7 gone) |
| Block 4 (middleware × 4) | `uv run mypy app` | 20 errors (9 gone; resolved `RequestResponseEndpoint` import path issue) |
| Block 5 (main.py + logger_config) | `uv run mypy app` | 14 errors (6 gone) |
| After health_check `dict[str,str] \| JSONResponse` issue | `uv run mypy app` | 15 errors (regression caught; `health_check` returned to `-> Response`, the 200 branch wrapped in `JSONResponse`) |
| Block 6 (error_handling × 14) | `uv run mypy app` | **0 errors** |
| Pre-merge gate | `uv run python .harness/verify.py --root . --when push` | **exit 0**: format 1164ms, lint 495ms, types 81102ms, tests 8877ms |
| CI workflow run #32819412857 | `quality` + `tests` jobs | **both pass**: 30s + 50s |

## Lessons learned

### 1. The pre-commit `mirrors-mypy` hook was structurally incompatible with strict mode

`mirrors-mypy` declares `language: python`, which spins up an isolated venv with only mypy + the listed `additional_dependencies`. After strict activation, mypy in that venv saw all of FastAPI, Starlette, loguru, and pydantic as `Any`, because none of those were in the venv. Result: 29 false positives in files that were clean in `mypy app`.

Three options were considered:

| Option | Verdict |
|--------|---------|
| List every dep in `additional_dependencies` | Rejected: brittle maintenance, drifts the moment anyone adds a dep to `pyproject.toml`. |
| `language: system` + `mypy` on `PATH` | Rejected: requires every contributor to have mypy globally installed, which violates the harness principle that no global tools are needed (everything via `uv`). |
| Remove the mypy hook | **Chosen.** The CI workflow already runs `mypy app` via `harness verify --when ci` after `uv sync --frozen`, which installs the real `pyproject.toml` deps. That is the single source of truth for the `types` gate, declared in `.harness/verify.toml`. Local pre-commit keeps ruff (which works fine in isolation). |

### 2. `RequestResponseEndpoint` lives in `starlette.middleware.base`, not `starlette.types`

Initial instinct was to import it from `starlette.types`. `mypy app` showed it as `Module "starlette.types" has no attribute "RequestResponseEndpoint"`. Moved to `from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint` and the errors cleared. Worth documenting because the Starlette docs use it without making its location obvious.

### 3. loguru's `Logger` class is type-only

`from loguru import Logger` fails at runtime because the Cython class is not re-exported. The `.pyi` declares it at the top-level, so it's available to mypy. The standard pattern is:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Logger


def setup_logger() -> Logger:
    ...
```

`from __future__ import annotations` makes the `-> Logger` reference lazy, so the string isn't resolved at runtime.

### 4. `dict[str, str] | JSONResponse` is **not** a valid return annotation for FastAPI handlers

FastAPI uses the return annotation to build the OpenAPI response model. Pydantic refuses `dict | JSONResponse` because `JSONResponse` is not a Pydantic field type. Symptom at import time:

```
fastapi.exceptions.FastAPIError: Invalid args for response field!
Hint: check that dict[str, str] | starlette.responses.JSONResponse is a
valid Pydantic field type.
```

Fix: either use `-> Response` (the broad Starlette base — FastAPI accepts this) or use `-> JSONResponse` only (and convert dicts at the call site). We chose the former for `health_check` and harmonised the 200-branch return to `JSONResponse(content=...)` so behaviour is identical from the client's view.

### 5. Always verify with the actual harness gate, not just the tool

`mypy app` alone passes, but `.harness/verify.py --when push` runs four gates (format, lint, types, tests) and is what the CI uses. Running the full local gate catches regressions (e.g., a type change that ruff rejects, or a behaviour change that breaks a unit test) that single-tool runs miss.

### 6. Single commit for an indivisible change

The change "enable strict + fix all 42 errors" is one conceptual unit. Splitting into "enable strict" + "fix errors" would leave commit 1 red on CI, which violates the principle that every commit on `main` is green. Single commit `chore(types): ...` was the correct call.

## Open follow-ups

None required by this PR. Two potential future improvements (out of scope):

1. **Run ruff format on pre-commit** (currently `--check` only) — would auto-format staged files. Already an open debate in the project's `docs/pr-conventions.md`.
2. **Pre-commit hook for `mypy app` via `uv run`** — would require a wrapper script that bypasses the venv isolation. Not needed because CI covers it.

## Appendix: commit graph

```
5b212c5  chore(harness): aplicar el estandar del MauriDev Harness (#111)
b56886a  chore(types): enable mypy strict and fix 42 type errors (#113)  ← this PR
```

## Appendix: verification commands run

```bash
# Baseline
uv run mypy app --no-incremental --follow-imports=silent
# → 42 errors in 12 files

# Per-block checkpoints
uv run mypy app --follow-imports=silent

# Full local gate (matches CI job 'quality')
uv run python .harness/verify.py --root . --when push
# → exit 0

# Individual gates
uv run ruff check app
uv run ruff format --check app
uv run mypy app
uv run pytest -q -m unit

# CI checks
gh pr checks 113 --repo MauriDev94/Api_monolith
gh run view 32819412857 --repo MauriDev94/Api_monolith --json status,conclusion
```
