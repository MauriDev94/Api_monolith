# Progreso de Remediación — Production-Readiness

Estado del plan de remediación derivado de [AUDIT_PRODUCTION_READINESS.md](history/AUDIT_PRODUCTION_READINESS.md).
Flujo: cada fase = 1 issue + 1 PR (`Closes #N`). Tests sobre Postgres real (testcontainers),
gate `--cov-branch --cov-fail-under=85`, gate de no-drift (`alembic check`) activo.

## ✅ Completado

| Fase | PR | Qué se hizo |
|------|----|-------------|
| Docs | #68 | Auditoría de los 4 bloques |
| Infra | #66 | `DATABASE_URL` + `render.yaml` |
| 1 | #70 | Red de tests en Postgres (testcontainers) + fix drift `due_date` (O1) + test de reuso |
| 2 | #72 | A2 rehidratación Todo · O2 fail-fast migración · O3 `/health` 503 |
| 3a | #74 | S1 rate limiting + O12 proxy headers · S4 logs · S6 500 · S7 HSTS/CSP · S8 InvalidHash |
| — | #76 | EnvConfig acepta solo `DATABASE_URL` (Codex #66) |
| 3b | #78 | S2 CSRF OAuth `state` · S5 OTP con HMAC |
| 4a | #80 | Eliminada feature `notifications` + huérfanos |
| 4b | #82 | Reconciliación de esquema (FKs, `google_id`, índice) + gate de no-drift |
| 4c | #84 | Puerto `UserProvider` (A1): `auth` desacoplado de la infra de `users` |
| 4d | #86 | Excepciones de dominio (`DomainError`, T4) + quitar alias duplicados (T7) |
| 5 (parcial) | #88 | **Body-size limit middleware** + connection pool (`pool_pre_ping`/`pool_recycle`, O5) + este doc |
| 5 | #90 | **O4**: eliminado `GET /v1/users` (listado, PII leak) + paginación `limit`/`offset` en `GET /v1/todos` (`total`, `limit`, `offset` en la respuesta) |
| 5 | #92 | **O8**: `DELETE` devuelve `204 No Content` sin body (antes `200` + `{"message": ...}`) |
| — | #94 | **Startup resiliente**: reintentos con backoff ante DB inalcanzable · fail-fast preservado ante errores de esquema · modo degradado (`/health` → 503) si la DB no vuelve, en vez de crash-loop · `docker-compose` sin auto-start |

Cobertura ~85% (gate `fail_under=85` en `pyproject.toml`). Los 4 bloques de la auditoría: remediados.

## ⏳ Pulido restante (bajo valor / opcional)

Pendiente para una ronda posterior (no bloquea producción):

- **O7** — Versionado de API inconsistente (`/auth/v1` vs `/v1/users`). ⚠️ Cambiar URLs es disruptivo para el frontend desplegado; evaluar antes.
- **TrustedHostMiddleware** — opcional, bajo impacto (la API no genera URLs basadas en Host).
- **GZipMiddleware** — saltable (payloads chicos).
- **`render.yaml` desalineado** — declara `runtime: python` y un bloque `databases: monolith-db` que ya no existe (la DB vive en Neon). El servicio real corre en **Docker**. Candidato a su propio PR.

## ❌ Hallazgos invalidados

- **O9** — La auditoría afirmaba que Render no usaba el `Dockerfile` (deducido de `runtime: python` en `render.yaml`). **Es falso**: el dashboard de Render muestra el servicio con runtime **Docker**, así que el `CMD` del `Dockerfile` es lo que corre en producción y el `startCommand` de `render.yaml` **no aplica**. Cualquier cambio de flags de arranque va en el `Dockerfile`.

### No tocar
- **O10** — La migración vacía `368a38931a3f` es ruido pero **ya está aplicada en prod** (`alembic_version`); quitarla del chain rompería Alembic. Dejarla.
