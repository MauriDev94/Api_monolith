<!-- harness:base -->

# MauriDev Harness

> Esta sección es mantenida por el MauriDev Harness. Si la editas a mano,
> la próxima actualización del harness puede sobrescribirla. Para reglas
> propias del proyecto, agregalas en la sección de más abajo.

Este proyecto adopta el estándar del MauriDev Harness: un gate de calidad
determinista que corre `ruff` + `mypy` + `pytest` y reporta el resultado
como exit code (no como opinión del agente).

## El gate

```
python .harness/verify.py --root .       # gate completo (lee .harness/verify.toml)
python .harness/verify.py --only lint    # un solo gate
python .harness/verify.py --when push    # lo que corre en pre-push
make check                              # atajo que delega en harness verify
```

Tres puertas invocan el mismo gate, declaradas una sola vez en
`.harness/verify.toml`:

- **`make check`** — entrada humana
- **`.harness/verify.py`** — entrada del agente (hooks)
- **`.github/workflows/ci.yml`** — entrada automatizada

El pre-push hook (`.githooks/pre-push`) bloquea con exit 1 si un gate
fatal falla. Activar una vez por clon: `git config core.hooksPath .githooks`.

## Convenciones de commits

Conventional Commits estricto. Tipos: `feat`, `fix`, `refactor`, `test`,
`docs`, `chore`, `style`, `perf`, `build`, `ci`. Scope opcional, scope
del harness: `harness`, `deps`, `lint`, `types`, `agents`.

## Memoria técnica

Decisiones de arquitectura → `docs/adr/NNNN-slug.md`, numeradas
secuencialmente, no se editan una vez aceptadas. Una decisión que cambia
se supersede con un ADR nuevo que la referencia.

Fronteras de módulo y reglas de dependencia → `docs/architecture/`.

## Lo que NO hace el harness

- No reescribe tu código de dominio
- No mergea PRs
- No toma decisiones arquitectónicas

<!-- /harness:base -->

---

<!-- harness:project -->

# Reglas específicas del proyecto (Monolith)

## Stack

FastAPI + Clean Architecture + DDD + PostgreSQL (Neon en producción,
testcontainers en integración), SQLAlchemy async, Pydantic v2, JWT auth.

## Estructura

```
app/
├── main.py
├── core/
│   ├── config/
│   ├── data/source/local/
│   ├── exceptions/
│   ├── middleware/
│   └── providers/
└── features/
    ├── auth/
    ├── todos/
    └── users/
        ├── domain/          # Entities, Value Objects
        ├── application/     # Use Cases, DTOs, Contracts
        ├── infrastructure/  # Repositories, Models, Mappers
        ├── presentation/    # API, Schemas, Mappers
        └── di/              # Dependencies
```

## Dirección de dependencias (estricta)

```
presentation → application → domain
infrastructure → application + domain
domain → nada
```

**Prohibiciones:**

- `domain` importa `fastapi`, `sqlalchemy`, `pydantic`
- `application` importa desde `infrastructure` o `presentation`
- `presentation` accede a repositorios directamente

## Flujo de trabajo

SDD (Spec-Driven Development) para features de tamaño medio/grande,
directo al código para fixes chicos. Ver `contributing.md` para el
flujo de Git (ramas, PRs, merge).

```
SDD: sdd-explore → sdd-propose → sdd-spec → sdd-design → sdd-tasks → sdd-apply → sdd-verify → sdd-archive
Git: main actualizado → rama feature → commit conventional → PR → squash merge → cleanup
```

## Tests

```
tests/
├── conftest.py                    # Fixtures globales
├── core/                          # Tests de core (main, database)
├── features/
│   ├── auth/
│   │   ├── domain/                # Entity tests (sin mocks)
│   │   ├── application/           # Use case tests (mock contratos)
│   │   ├── infrastructure/        # Repository tests (DB real)
│   │   └── presentation/          # API tests (HTTP client)
│   ├── todos/
│   └── users/
└── e2e/                           # End-to-end tests
```

Markers: `unit` (default, sin Docker), `integration` (requiere DB),
`e2e` (requiere stack completo). `--strict-markers` está activo,
typos en markers fallan el gate.

## Naming conventions

| Elemento | Patrón | Ejemplo |
|----------|--------|---------|
| Entidad | PascalCase | `User`, `Todo` |
| Value Object | PascalCase | `Email` |
| Use Case | `VerbNombreUseCase` | `CreateTodoUseCase` |
| Schema | `NombreResponse` | `UserResponse` |
| Test | `test_<behavior>_when_<condition>` | `test_email_raises_when_invalid` |

## Skills inyectados en sub-agentes

| Contexto | Skills |
|----------|--------|
| Implementación FastAPI | `clean-architecture-ddd` + `fastapi-api-patterns` |
| Testing | `python-testing-patterns` + `clean-architecture-ddd` |
| Auth | `auth-security-patterns` |

<!-- /harness:project -->
