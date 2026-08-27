# Roadmap — Monolith API a MVP Profesional

**Última actualización:** 2026-07-04
**Estado general:** ✅ En producción (Render) · remediación de production-readiness completada

---

## Resumen de Progress

| Fase | Prioridad | Estado |
|------|-----------|--------|
| 1. Correcciones Críticas | 🟢 | ✅ Completado |
| 2. SDD + Observabilidad | 🟢 | ✅ Completado |
| 3. Testing + Coverage | 🟢 | ✅ Completado (92% line en su momento; hoy gate 85% branch) |
| 4. Recordatorios (TODOs) | 🟢 | ⏸️ Feature `notifications` **eliminada** en Fase 11 (#80) |
| 5. Newsletter | 🟢 | ⏸️ Eliminado (no aporta al portafolio) |
| 6. Deploy | 🟢 | ✅ Completado (Render + PostgreSQL en Neon) |
| 7. Refactor Notifications | 🟢 | ⏸️ Superado — la feature se **eliminó** después (#80) |
| 8. OTP Password Reset | 🟢 | ✅ Completado (endurecido a HMAC en #78) |
| 9. Email Notifications | 🟢 | ⏸️ Superado — ligado a `notifications`, **eliminada** (#80) |
| 10. Google SSO Login | 🟢 | ✅ Completado (CSRF `state` validado en #78) |
| **11. Remediación Production-Readiness** | 🟢 | ✅ **Completado (auditoría 4 bloques → PRs #66–#94)** |

> **Nota:** las Fases 4/7/9 giraban en torno a la feature `notifications`, que fue **eliminada** durante la Fase 11 (dead code / YAGNI). Se conservan aquí como registro histórico; el diseño original vive en `docs/history/`.

---

## Fase 1: Correcciones Críticas

**Prioridad:** 🔴 AHORA

### 1.1 — Arreglar Email VO para permitir `+` tags
**Estado:** ✅ Completado (2026-04-10)

- [x] Regex actualizado en `email.py` línea 14
- [x] Tests actualizados para reflejar comportamiento correcto
- [x] Suite completa passing: 153 tests

---

### 1.2 — Unificar versión Python
**Estado:** ✅ Completado (2026-04-10)

- [x] Unificar a Python 3.12 (recomendado — LTS, mejor soporte libraries)
- [x] Actualizar `.github/workflows/tests.yml` de 3.13 → 3.12
- [x] Verificar Dockerfile ya usa 3.12-slim ✅
- [ ] Actualizar `requirements.txt` si hay incompatibilidades
- [x] Correr tests en verde después del cambio (PR #3)

**Archivos a modificar:**
- `.github/workflows/tests.yml` (línea 20)

---

### 1.3 — Crear `.env.example`
**Estado:** ✅ Completado (2026-04-10)

- [x] Copiar estructura de `.env` sin valores reales
- [x] Documentar cada variable con comentario
- [x] Agregar a `.gitignore` si no está ✅ (ya estaba)

**Variables necesarias:**
```env
DB_USER=
DB_PASSWORD=
DB_NAME=
DB_PORT=
DB_HOST=
JWT_SECRET_KEY=

# SMTP (opcional para OTP real)
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_SENDER_EMAIL=
SMTP_USE_TLS=true
```

---

### 1.4 — Agregar validaciones extra de seguridad
**Estado:** ✅ Completado (2026-04-10)

- [x] Password mínimo 8 caracteres con complejidad (letras + números)
- [x] Rate limiting global disponible (middleware creado)
- [x] CORS configurado explícitamente
- [x] Headers de seguridad (X-Content-Type-Options, etc.)

---

## Fase 2: SDD + Observabilidad

**Prioridad:** 🟡 Esta semana

### 2.1 — Inicializar SDD
**Estado:** ✅ Completado (2026-04-11)

- [x] Crear estructura `.atl/`
- [x] Configurar artifact store (engram)
- [x] Generar `skill-registry` local en `.atl/skill-registry.md`
- [ ] Definir cambios activos y specs (siguiente: `sdd-propose` para deploy)

**Artifacts de 2.1:**
- `.atl/skill-registry.md`
- `Engram: sdd-init/Monolith`
- `Engram: sdd/Monolith/testing-capabilities`

---

### 2.2 — Corregir AGENTS.md
**Estado:** ✅ Completado (2026-04-12)

- [x] Reemplazar enfoque acoplado a un solo runtime por convención agnóstica (Codex/OpenCode)
- [x] Documentar resolución de agents/skills por entorno
- [x] Confirmar política local-only para agents/skills y artefactos SDD

---

### 2.3 — Logging estructurado + auditoría de cobertura por feature
**Estado:** 🚧 En progreso (2026-04-12)

- [x] Correlación `request_id` en middleware + handlers globales
- [x] Formato JSONL estructurado disponible para observabilidad
- [x] Log levels base definidos (INFO/WARNING/ERROR)
- [x] Loguear queries lentas de DB (completado en 2.4)
- [x] Ejecutar auditoría de cobertura para validar casos de uso por feature

**Resultado de auditoría (2026-04-12):**
- Coverage total actual: **90%** (`pytest --cov=app --cov-report=term-missing -q`)
- Casos de uso de `auth/users/todos`: cobertura alta (en general **93% a 100%** en application use cases)
- Gap principal: infraestructura (repositories) y bootstrap/runtime (`app/main.py`, `database.py`)

**Conclusión técnica:**
- ✅ Se cubre la mayoría de casos de uso funcionales por feature
- ⚠️ Falta fortalecer observabilidad/performance de DB (slow queries) y casos de infraestructura

**Archivos a modificar:**
- `app/core/middleware/request_context.py`
- `app/core/config/logger_config.py`

---

### 2.4 — Logging de queries lentas de DB
**Estado:** ✅ Completado (2026-04-13)

- [x] Implementar event listeners en `database.py` para before/after cursor execute
- [x] Agregar threshold configurable (1.0s por defecto)
- [x] Loguear queries que excedan el threshold con WARNING y metadata (slow_query: true, duration)
- [x] Desactivar `echo=True` en engine para evitar ruido en logs

**Archivo modificado:**
- `app/core/data/source/local/database.py`

**Resultado:** Queries lentas ahora se loguean automáticamente en `logs/app_YYYY-MM-DD.log` con nivel WARNING y contexto de duración.

---

## Fase 3: Testing + Coverage

**Prioridad:** 🟡 Esta semana

### 3.1 — Completar tests de infraestructura auth
**Estado:** ✅ Completado (2026-04-13)

- [x] `OtpRepository` integration tests (ya existían)
- [x] `TokenRevocationRepository` integration tests (6 tests creados)

**Nota:** `RefreshTokenRepository` no existe en el código — se usa `TokenRevocationRepository`.

**Archivos creados:**
- `tests/features/auth/infrastructure/repositories/test_token_revocation_repository.py`

---

### 3.2 — Agregar tests de dominio todos
**Estado:** ✅ Completado (2026-04-13)

- [x] `test_todo_entity.py` (ya existía con 6 tests)
- [x] Coverage para edge cases (normalize, empty validation, mutation methods)

**Tests existentes:**
- test_should_normalize_todo_text_fields
- test_should_convert_blank_description_to_none
- test_should_raise_when_required_text_field_is_empty (parametrized)
- test_should_mutate_todo_with_behavior_methods
- test_should_raise_when_renaming_todo_with_invalid_title

**Resultado:** 6 tests passing ✅

---

### 3.3 — Subir coverage mínimo a 80%
**Estado:** ✅ Completado (2026-04-13)

- [x] Coverage actual: **92%** (target 80% excedido)
- [x] Auditoría de tests completada (159 tests)
- [x] Tests agregados para coverage gaps:

**Tests creados:**
- `tests/core/test_main.py` (5 tests): healthcheck, custom_openapi, BearerAuth
- `tests/core/test_database.py` (6 tests): slow query logging, engine config

**Coverage por capa:**
- Domain: 95%+
- Application use cases: 95%+
- Infrastructure: 75-95%
- Presentation (API): 91-96%
- Core (main, database): 92%

**Resultado:** 170 tests passing ✅

---

## Fase 4: Sistema de Recordatorios de TODOs

**Prioridad:** 🟡 Antes del Deploy

### 4.1 — Agregar due_date a Todo
**Estado:** ✅ Completado (2026-04-15)

- [x] Agregar campo `due_date` al dominio de `Todo` (nullable, no pasado, timezone-aware)
- [x] Agregar `due_date` al TodoModel
- [x] Actualizar mappers, DTOs, schemas
- [x] Agregar 6 tests para due_date (12 total en entity)

**Archivos modificados:**
- `app/features/todos/domain/entities/todo.py`
- `app/features/todos/infrastructure/models/todo_model.py`
- `app/features/todos/infrastructure/mappers/todo_mapper.py`
- `app/features/todos/application/dto/create_todo_params.py`
- `app/features/todos/application/dto/update_todo_params.py`
- `app/features/todos/presentation/schemas/todo_requests.py`
- `app/features/todos/presentation/schemas/todo_responses.py`
- `app/features/todos/presentation/mappers/todo_mapper.py`
- `tests/features/todos/domain/test_todo_entity.py`

**Resultado:** 165 tests passing ✅

---

### 4.2 — Notification Domain
**Estado:** ✅ Completado (2026-04-15)

- [x] Crear `Notification` entity con NotificationType, NotificationStatus
- [x] Crear `NotificationRepository` con método factory `create_for_todo_reminder()`
- [x] Crear modelo `NotificationModel` y mappers
- [x] Crear API endpoints: `GET /notifications`, `PATCH /notifications/{id}/read`

**Archivos creados:**
- `app/features/notifications/domain/entities/notification.py`
- `app/features/notifications/application/contracts/notification_store.py`
- `app/features/notifications/infrastructure/models/notification_model.py`
- `app/features/notifications/infrastructure/repositories/notification_repository.py`
- `app/features/notifications/infrastructure/mappers/notification_mapper.py`
- `app/features/notifications/presentation/schemas/notification_schemas.py`
- `app/features/notifications/presentation/mappers/notification_mapper.py`
- `app/features/notifications/presentation/api.py`

**Resultado:** Tests passing ✅

---

### 4.3 — Scheduler de Recordatorios
**Estado:** ✅ Completado (2026-04-15)

- [x] Implementar job de recordatorios (process_reminders)
- [x] Query de TODOs con due_date próximo (próximo día por defecto)
- [x] Crear notification para cada recordatorio
- [x] Endpoint interno para testing (POST /internal/reminders/process)

**Nota:** Email no implementado aún — se puede agregar después usando SMTP existente.

**Archivos creados:**
- `app/features/notifications/application/usecases/process_reminders_use_case.py`

---

### 4.4 — Endpoints de Notificaciones
**Estado:** ✅ Completado (en 4.2)

- [x] GET `/notifications` (listar notificaciones del usuario)
- [x] PATCH `/notifications/{id}/read` (marcar como leída)

---


## Fase 5: Deploy

**Prioridad:** 🟢 Completado (2026-04-20)

### 5.1 — Dockerfile multi-stage
**Estado:** ✅ Completado

- [x] Dockerfile existente ya optimizado (python:3.12-slim)
- [x] Healthcheck integrado
- [x] Usuario no-root

---

### 5.2 — Configurar plataforma de deploy
**Estado:** ✅ Completado (2026-04-20)

- [x] Elegir: **Render** (100% gratis sin CC)
- [x] Healthcheck `/health` con DB ping
- [x] PostgreSQL managed — hoy en **Neon** (free tier, PG 16), no en Render: la Postgres free de Render se **auto-elimina a los ~30 días**, lo que tumbó producción el 2026-08-05. Neon suspende el compute por inactividad pero no borra la base. Se apunta vía `DATABASE_URL` (endpoint directo, `?sslmode=require`) sin cambios de código.
- [x] Variables de entorno configuradas
- [x] Auto-create tables en startup (workaround para free tier)

**URL en producción:** https://api-monolith.onrender.com

**Funcionalidades verificadas:**
- Registro usuario → 201 ✅
- Email duplicado → 409 ✅
- Health check → 200 ✅

---

### 5.3 — Workflow CD
**Estado:** 📋 Planificado

- [ ] GitHub Actions para deploy automático
- [ ] Build → Test → Deploy en Render

**Nota:** El deploy actual es automático con push a main (auto-deploy enabled).
**Archivo a crear (opcional):** `.github/workflows/deploy.yml`

---

## Fase 6: Polish

**Prioridad:** 🟢 Después del MVP

### 6.1 — OpenAPI custom info
**Estado:** ✅ Completado (2026-04-21)

- [x] Título descriptivo
- [x] Descripción de API
- [x] Información de contacto
- [x] Licencia

**Archivo a modificar:** `app/main.py`

---

### 6.2 — Documentación
**Estado:** ✅ Completado (2026-04-21)

- [x] README con estado real del proyecto
- [x] Borrar secciones de roadmap viejo
- [x] Agregar badges: coverage, deploy, Python version

**Archivo a modificar:** `README.md`

---

### 6.3 — Cleanup técnico
**Estado:** ✅ Completado (2026-04-27)

- [x] Dependencias outdated en `requirements.txt` (actualizadas a versiones vigentes, 2026-04-27)
- [x] Limpiar imports no usados
- [x] Actualizar pre-commit hooks si es necesario (ruff-format + bumps de versiones)

---

## Fase 7: Refactor Feature Notifications

**Prioridad:** 🟡 Siguiente iteración

### 7.1 — Diagnóstico y diseño del refactor
**Estado:** ✅ Completado (2026-04-27)

- [x] Auditar responsabilidades por capa (domain/application/infrastructure/presentation/di)
- [x] Detectar duplicaciones y acoplamientos con todos/reminders
- [x] Definir matriz de contratos API no rompibles (compatibilidad y deprecaciones)
- [x] Definir criterios de aceptación técnicos por capa (DoD por domain/application/infrastructure/presentation/di)
- [x] Definir estrategia de compatibilidad **opción B**: refactor + ajustes API versionados

**Artifacts 7.1:**
- `docs/history/SDD_PROPOSAL_PHASE7_NOTIFICATIONS.md`
- `docs/PHASE7_1_NOTIFICATIONS_AUDIT.md` (histórico)

### 7.2 — Refactor por capas
**Estado:** ✅ Completado (2026-04-27, PRs #25-#28)

- [x] Domain: invariantes y claridad de estados/eventos de notificación
- [x] Application: casos de uso más explícitos y consistentes
- [x] Infrastructure: repositorio/mappers más robustos + errores homogéneos
- [x] Presentation: contratos API, validaciones y respuestas consistentes
- [x] DI: providers limpios y testeables

### 7.3 — Calidad y cobertura del refactor
**Estado:** ✅ Completado (2026-04-29, PR #29)

- [x] Cobertura de tests de notifications >= 90% en casos críticos
- [x] Casos borde: ownership, idempotencia, race conditions y estados inválidos
- [ ] Revisión final de observabilidad (logs con request_id y errores trazables)

---

## Fase 8: OTP Password Reset

**Prioridad:** ✅Completado

**Estado:** ⏳ Pendiente (debug SMTP) → ✅ Completado (2026-04-30) con Resend

---

## Fase 9: Email Notifications (Todo Reminders)

**Prioridad:** 🟡 Esta semana

### 9.1 — Configuración de entorno
**Estado:** ✅ Completado (PR #35)

- [x] Agregar `internal_api_key` a `env_config.py`
- [x] Agregar `INTERNAL_API_KEY` a `.env.example`

### 9.2 — Extender contrato EmailSender
**Estado:** ✅ Completado (PR #36)

- [x] Agregar método abstracto `send_reminder(to_email, todo_title, due_date)` a `EmailSender`
- [x] Actualizar `ResendEmailSender` con implementación
- [x] Actualizar `ConsoleEmailSender` con implementación
- [x] Actualizar `SmtpEmailSender` con implementación (backwards compat)
- [x] Actualizar `CaptureEmailSender` (tests E2E) con implementación no-op

### 9.3 — Template HTML para reminders
**Estado:** ✅ Completado (en PR #36)

- [x] Definir template consistente con estilo OTP
- [x] Agregar `REMINDER_HTML_TEMPLATE` en `ResendEmailSender`

### 9.4 — Actualizar ProcessRemindersUseCase
**Estado:** ✅ Completado (PR #37)

- [x] Agregar `AuthDatasource` como dependencia
- [x] Agregar `EmailSender` como dependencia
- [x] Implementar flujo: crear notificación → enviar email → marcar SENT
- [x] Manejo de errores: dejar en PENDING para reintento
- [x] Loguear warnings cuando user no existe

### 9.5 — Endpoint interno protegido
**Estado:** ✅ Completado (PR #38)

- [x] Crear `/internal/v1/reminders/process` endpoint
- [x] Proteger con `X-Internal-Token` header
- [x] Validar que retorna 401 sin token válido
- [x] Validar que retorna 200 con `{ processed, created, sent, failed }`

### 9.6 — Actualizar DI dependencies
**Estado:** ✅ Completado (PR #40)

- [x] Agregar `get_process_reminders_use_case` provider
- [x] Verificar imports de `get_todo_repository`, `get_auth_repository`, `get_email_sender`

### 9.7 — Tests unitarios
**Estado:** ✅ Completado (PR #41)

- [x] 6 tests unitarios para ProcessRemindersUseCase

### 9.8 — Integración y validación
**Estado:** ⏳ Pendiente

- [ ] Suite completa pasa (sin regresiones)
- [ ] Configurar cron-job.org con URL y header

---

## 🚧 PROPOSAL MODE: 9.8 Integración y validación

## Fase 10: Google SSO Login

**Prioridad:** 🟡 Alta
**Estado:** ✅ Completado
**Spec:** `docs/history/SDD_PROPOSAL_PHASE10_GOOGLE_SSO.md`

---

### 10.1 — Domain: User.password_hash nullable
**Estado:** ✅ Completado

- [x] `password_hash: str | None` en `User`
- [x] `__post_init__`: omitir validación cuando es `None`
- [x] `change_password_hash(new_hash: str) -> None`
- [x] `google_id: str | None` columna
- [x] `birthdate` nullable para usuarios Google
- [x] Tests de dominio actualizados

---

### 10.2 — Migration: google_id + password_hash nullable
**Estado:** ✅ Completado

- [x] `ADD COLUMN google_id VARCHAR(255) UNIQUE NULLABLE`
- [x] `ALTER COLUMN password_hash DROP NOT NULL`
- [x] Alembic revision: `fe8f9c0d1b3e_add_google_id_nullable_password.py`
- [x] Alembic revision: `make_birthdate_nullable.py`

---

### 10.3 — Application: contratos y DTOs
**Estado:** ✅ Completado

- [x] `OAuthProvider` (contrato)
- [x] `GoogleAuthDatasource` (contrato)
- [x] `GoogleUserInfo`, `GoogleTokenData` (DTOs)
- [x] `InitiateGoogleLoginUseCase`
- [x] `HandleGoogleCallbackUseCase`
- [x] `LinkGoogleAccountUseCase`

---

### 10.4 — Infrastructure: GoogleOAuthProviderImpl
**Estado:** ✅ Completado

- [x] `GoogleOAuthProviderImpl` con `httpx`
- [x] `StubGoogleOAuthProvider` para tests
- [x] Variables de entorno en `EnvConfig` y `.env.example`

---

### 10.5 — Infrastructure: GoogleAuthRepository
**Estado:** ✅ Completado

- [x] `create_google_user` con `password_hash=None`
- [x] `get_user_by_google_id`
- [x] `get_user_by_id`
- [x] `link_google_id`
- [x] Integration tests con `db_session` (6 tests)

---

### 10.6 — Presentation + DI
**Estado:** ✅ Completado

- [x] `GET /auth/v1/google` → redirect
- [x] `GET /auth/v1/google/callback` → tokens
- [x] `POST /auth/v1/link-google` → vincular cuenta
- [x] DI providers en `auth/di/dependencies.py`
- [x] Schemas: GoogleInitResponse, GoogleCallbackRequest, GoogleLinkAccountRequest
- [x] Variables de entorno documentadas en `.env.example`

---

### 10.7 — E2E tests
**Estado:** ✅ Completado

- [x] Flujo nuevo → crea usuario + retorna tokens
- [x] Segundo login mismo Google account → mismo `user_id`
- [x] Email con password existente → 409
- [x] Suite completa en verde (234 tests)

---

## Fase 11: Remediación Production-Readiness

**Prioridad:** 🟢 Completado
**Estado:** ✅ Completado (PRs #66–#94)
**Fuente:** `docs/REMEDIATION_PROGRESS.md` · auditoría: `docs/history/AUDIT_PRODUCTION_READINESS.md`

Auditoría formal de 4 bloques (arquitectura, seguridad, testing, operación) y remediación por fases (cada fase = 1 issue + 1 PR):

- **#70 (Fase 1)** — Red de tests sobre **Postgres real** (testcontainers) + fix drift `due_date` (O1) + `--cov-branch`.
- **#72 (Fase 2)** — Rehidratación de `Todo` sin lanzar (A2) · migración en startup **fail-fast** (O2, después matizado en #94) · `/health` → 503 (O3).
- **#74 (Fase 3a)** — Rate limiting registrado + IP real desde `X-Forwarded-For` (S1/O12) · logs sanitizados (S4) · 500 sin `str(exc)` (S6) · HSTS/CSP (S7) · `InvalidHash` (S8).
- **#78 (Fase 3b)** — CSRF OAuth `state` validado (S2) · OTP con HMAC-SHA256 (S5).
- **#80 (Fase 4a)** — **Eliminada la feature `notifications`** (dead code / YAGNI).
- **#82 (Fase 4b)** — Reconciliación de esquema (FKs, índices) + **gate de no-drift** (`alembic check`).
- **#84 (Fase 4c)** — Puerto **`UserProvider`**: `auth` desacoplado de la infra de `users` (A1).
- **#86 (Fase 4d)** — Excepciones de dominio (`DomainError`, T4) + quitar alias duplicados (T7).
- **#88 (Fase 5)** — Body-size limit middleware + connection pool (`pool_pre_ping`/`pool_recycle`, O5).
- **#90 (Fase 5)** — Eliminado `GET /v1/users` (fuga de PII, O4) + paginación en `GET /v1/todos`.
- **#92 (Fase 5)** — `DELETE` devuelve **204 No Content** sin body en vez de `200` + `{"message": ...}` (O8).
- **#94** — **Startup resiliente**: reintentos con backoff ante DB inalcanzable, fail-fast preservado ante errores de esquema, arranque en **modo degradado** (`/health` → 503) si la DB no vuelve, en vez de crash-loop. Además `docker-compose` sin auto-start.

**Resultado:** los 4 bloques de la auditoría remediados; branch coverage gate en 85% (`pyproject.toml`: `fail_under = 85`).

---

## Notas de Deploy

### Alembic en Startup (Free Tier)
**Decisión consciente:** El `startup_event` en `app/main.py` ejecuta `alembic upgrade head` en cada deploy.

**Trade-off:**
- ✅ Garantiza que las migraciones se corren sin acceso shell
- ✅ No necesita herramientas externas (como Render CLI)
- ⚠️ Cada deploy corre alembic aunque no haya migraciones nuevas (overhead mínimo)
- ✅ **Arranque resiliente** (#72 fail-fast, matizado en #94). El comportamiento hoy distingue dos fallas:
  - **DB inalcanzable** (DNS/conexión, `OperationalError`) → reintentos con backoff lineal. Cubre el caso transitorio de la DB que aún no está lista.
  - **Error de esquema/migración** con la DB alcanzable → **fail-fast**: no arrancar sirviendo contra un esquema roto o a medias.
  - Si tras agotar reintentos la DB sigue caída → arranca en **modo degradado** y `/health` responde 503, en vez de crash-loopear. El proceso muriendo tapaba incluso `/health` y dejaba el incidente sin diagnóstico.

**Alternativas consideradas:**
- Render CLI con shell (requiere pago o trabajo manual)
- GitHub Actions workflow separado (complejidad adicional)
- Stamp + manual sync (no escalable para free tier)

**Para producción con acceso shell:** Remover el `alembic upgrade` del startup y usar deploy pipeline.

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-07-04 | 📚 Docs ordenados: históricos a `docs/history/`; README/README_ES/ARCHITECTURE/roadmap al día |
| 2026-06-24 | ✅ **Fase 11 completa: remediación production-readiness (PRs #66–#90)** — Postgres tests, rate limiting, CSRF, HMAC, UserProvider, `notifications` eliminada, paginación |
| 2026-05-05 | ✅ 10 completa: Google SSO Login funciona en producción (10.1-10.7) |
| 2026-05-05 | ✅ 10.1-10.5 completados: Domain, Migration, Contracts, Provider, Repository (#44-#46) |
| 2026-05-04 | 🚧 10 iniciada: Google SSO Login (propuesta + specs + design en docs/) |
| 2026-04-30 | ✅ 8 completado: OTP Password Reset con Resend (#32 + #33) |
| 2026-04-27 | ✅ 7.1 completado: auditoría por capas + matriz API + DoD + estrategia opción B |
| 2026-04-27 | ✅ 6.3 completado (dependencias + hooks actualizados, PR #22 merged) |
| 2026-04-27 | 🚧 7.1 iniciado con estrategia opción B (refactor + ajustes API versionados) |
| 2026-04-27 | 📝 Se redefine la fase siguiente: **Refactor Notifications** pasa a ser Fase 7 |
| 2026-04-24 | ✅ Fix de seguridad: CORS explícito, BearerAuth en endpoints públicos, health con SQLAlchemy text() |
| 2026-04-21 | ✅ 6.2: README actualizado (estado real, badges, endpoints, notificaciones) |
| 2026-04-21 | ✅ 6.1: OpenAPI custom info + fix de naming de contacto |
| 2026-04-20 | 🚀 **Deploy a producción (Render)!** - API live en https://api-monolith.onrender.com |
| 2026-04-20 | ✅ Fix: SQLAlchemy 2.0 event.listens_for compatibility |
| 2026-04-20 | ✅ Fix: ConflictError handler retorna 409 (handler global funciona) |
| 2026-04-20 | ✅ Fix: Auto-create tables en startup para Render free tier |
| 2026-04-13 | ✅ 3.3: Coverage 92% (11 tests nuevos para main + database) |
| 2026-04-13 | ✅ 3.2: Tests dominio Todo entity (6 tests ya existían) |
| 2026-04-13 | ✅ 3.1: Tests TokenRevocationRepository (6 tests) |
| 2026-04-12 | 🚧 2.3: Auditoría de logging + cobertura (90%, casos de uso cubiertos) |
| 2026-04-12 | ✅ 2.2: Convención agnóstica de agents/skills (Codex + OpenCode) |
| 2026-04-11 | ✅ 2.1: SDD inicializado en modo Engram + skill registry local |
| 2026-04-10 | ✅ Fix 1.4: Agrega validaciones de seguridad (PR #5) |
| 2026-04-10 | ✅ Fix 1.3: Agrega .env.example (PR #4 merged) |
| 2026-04-10 | ✅ Fix 1.2: Unifica Python 3.12 en CI (PR #3) |
| 2026-04-10 | ✅ Fix 1.1: Email VO permite `+` tags (PR #2 merged) |
| 2026-04-10 | 📝 Roadmap creado |

---

## Notas

- **Versión Python:** (CI: 3.12, Dockerfile: 3.12) ✅
- **Skills/agentes:** Convención agnóstica aplicada en AGENTS.md ✅
- **SDD:** Inicializado en modo Engram (local-first).
