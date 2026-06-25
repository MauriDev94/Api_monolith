# Progreso de Remediación — Production-Readiness

Estado del plan de remediación derivado de [AUDIT_PRODUCTION_READINESS.md](AUDIT_PRODUCTION_READINESS.md).
Flujo: cada fase = 1 issue + 1 PR (`Closes #N`). Tests sobre Postgres real (testcontainers),
gate `--cov-branch --cov-fail-under=82`, gate de no-drift (`alembic check`) activo.

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

Cobertura ~86.9%. Bloques 1-3 de la auditoría: remediados. Bloque 4: casi completo.

## ⏳ Pulido restante (Fase 5 — bajo valor / opcional)

Pendiente para una ronda posterior (no bloquea producción):

- **O7** — Versionado de API inconsistente (`/auth/v1` vs `/v1/users`). ⚠️ Cambiar URLs es disruptivo para el frontend desplegado; evaluar antes.
- **O8** — `DELETE` devuelve 200+body → debería ser 204.
- **O9** — El `Dockerfile` no lo usa Render (`runtime: python`); decidir si se mantiene para local o se elimina.
- **TrustedHostMiddleware** — opcional, bajo impacto (la API no genera URLs basadas en Host).
- **GZipMiddleware** — saltable (payloads chicos).

### No tocar
- **O10** — La migración vacía `368a38931a3f` es ruido pero **ya está aplicada en prod** (`alembic_version`); quitarla del chain rompería Alembic. Dejarla.
