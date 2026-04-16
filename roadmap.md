# Roadmap — Monolith API a MVP Profesional

**Última actualización:** 2026-04-11
**Estado general:** En progreso

---

## Resumen de Progress

| Fase | Prioridad | Estado |
|------|-----------|--------|
| 1. Correcciones Críticas | 🟢 | ✅ Completado |
| 2. SDD + Observabilidad | 🟢 | ✅ Completado |
| 3. Testing + Coverage | 🟢 | ✅ Completado (92% coverage) |
| 4. Recordatorios (TODOs) | 🟡 | 📋 Planificado |
| 5. Newsletter | 🟡 | 📋 Planificado |
| 6. Deploy | 🟢 | 📋 Planificado (Render + PostgreSQL) |
| 7. Polish | 🟢 | ⏳ Pendiente |

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

## Fase 5: Newsletter

**Prioridad:** 🟡 Antes del Deploy

### 5.1 — Newsletter Domain
**Estado:** 📋 Planificado

- [ ] Crear `Subscriber` entity
- [ ] Crear `Campaign` entity
- [ ] Crear `NewsletterTemplate` value object

**Archivos a crear:**
- `app/features/newsletter/domain/entities/subscriber.py`
- `app/features/newsletter/domain/entities/campaign.py`

---

### 5.2 — Newsletter Infrastructure
**Estado:** 📋 Planificado

- [ ] Crear `SubscriberRepository`
- [ ] Integrar con email sender existente (SMTP)

**Archivos a crear:**
- `app/features/newsletter/infrastructure/repositories/subscriber_repository.py`
- `app/features/newsletter/infrastructure/models/subscriber_model.py`

---

### 5.3 — Newsletter API
**Estado:** 📋 Planificado

- [ ] POST `/newsletter/subscribe`
- [ ] DELETE `/newsletter/unsubscribe`
- [ ] POST `/newsletter/send` (admin only)

**Archivo a crear:**
- `app/features/newsletter/presentation/api.py`

---

## Fase 6: Deploy

**Prioridad:** 🟡 Después de Features Nuevas

### 6.1 — Dockerfile multi-stage
**Estado:** 📋 Planificado

- [ ] Separar dev/prod stages
- [ ] Optimizar tamaño de imagen final
- [ ] Multi-platform support (opcional)

**Archivo a modificar:** `Dockerfile`

---

### 6.2 — Configurar plataforma de deploy
**Estado:** 📋 Planificado

- [x] Elegir: **Render** (recomendado por free tier + PostgreSQL incluido)
- [ ] Configurar PostgreSQL managed
- [ ] Variables de entorno en la plataforma
- [ ] Healthcheck profundo (`/health` con DB ping)

**Opciones evaluadas:**
| Plataforma | Pros | Cons |
|------------|------|------|
| Railway | Deploy automático, PostgreSQL incluido | Límite gratuito bajo ($5/mes) |
| Render ✅ | Free tier generoso (750h/mes), PostgreSQL incluido | Cold starts lentos |
| Fly.io | Multi-region | Configuración más compleja |

**Selección:** Render — suficiente para MVP, simple de configurar.

---

### 6.3 — Workflow CD
**Estado:** 📋 Planificado

- [ ] GitHub Actions para deploy automático
- [ ] Build → Test → Push → Deploy
- [ ] Notificaciones de deploy fallido

**Archivo a crear:** `.github/workflows/deploy.yml`

---

### 6.4 — Healthcheck profundo
**Estado:** 📋 Planificado

- [ ] Endpoint `/health` con DB ping
- [ ] Readiness vs Liveness probes separadas
- [ ] Métricas básicas (opcional)

**Archivo a modificar:** `app/main.py`

---

## Fase 7: Polish

**Prioridad:** 🟢 Después del MVP

### 5.1 — OpenAPI custom info
**Estado:** ⏳ Pendiente

- [ ] Título descriptivo
- [ ] Descripción de API
- [ ] Información de contacto
- [ ] Licencia

**Archivo a modificar:** `app/main.py`

---

### 5.2 — Documentación
**Estado:** ⏳ Pendiente

- [ ] README con estado real del proyecto
- [ ] Borrar secciones de roadmap viejo
- [ ] Agregar badges: coverage, deploy, Python version

**Archivo a modificar:** `README.md`

---

### 5.3 — Cleanup técnico
**Estado:** ⏳ Pendiente

- [ ] Dependencias outdated en `requirements.txt`
- [ ] Limpiar imports no usados
- [ ] Actualizar pre-commit hooks si es necesario

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-04-13 | 📋 Fase 4: Planificado - Render como plataforma, Docker multi-stage, CD workflow, /health |
| 2026-04-13 | ✅ 3.3: Coverage 92% (11 tests nuevos para main + database) |
| 2026-04-13 | ✅ 3.2: Tests dominio Todo entity (6 tests ya existían) |
| 2026-04-13 | ✅ 3.1: Tests TokenRevocationRepository (6 tests) |
<<<<<<< HEAD
| 2026-04-13 | ✅ 3.2: Tests dominio Todo entity (6 tests ya existían) |
=======
| 2026-04-13 | ✅ 2.4: Logging de queries lentas de DB (threshold 1.0s, event listeners) |
>>>>>>> c1a93a5 (docs(roadmap): actualiza Fase 3 como completada (92% coverage))
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
