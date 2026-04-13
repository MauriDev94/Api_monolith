# Roadmap — Monolith API a MVP Profesional

**Última actualización:** 2026-04-11
**Estado general:** En progreso

---

## Resumen de Progress

| Fase | Prioridad | Estado |
|------|-----------|--------|
| 1. Correcciones Críticas | 🟢 | ✅ Completado |
| 2. SDD + Observabilidad | 🟡 | 🚧 En progreso |
| 3. Testing + Coverage | 🟡 | ⏳ Pendiente |
| 4. Deploy | 🟢 | ⏳ Pendiente |
| 5. Polish | 🟢 | ⏳ Pendiente |

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
**Estado:** ⏳ Pendiente

- [ ] `OtpRepository` integration tests
- [ ] `RefreshTokenRepository` integration tests
- [ ] `TokenRevocationRepository` integration tests

**Archivos a crear:**
- `tests/features/auth/infrastructure/repositories/test_otp_repository.py`
- `tests/features/auth/infrastructure/repositories/test_refresh_token_repository.py`

---

### 3.2 — Agregar tests de dominio todos
**Estado:** ⏳ Pendiente

- [ ] `test_todo_entity.py`
- [ ] Coverage para edge cases

**Archivos a crear:**
- `tests/features/todos/domain/test_todo_entity.py`

---

### 3.3 — Subir coverage mínimo a 80%
**Estado:** ⏳ Pendiente

- [ ] Coverage actual: ~70% (ver en CI)
- [ ] Target: 80%
- [ ] Identificar gaps con `pytest --cov --cov-report=term-missing`

---

## Fase 4: Deploy

**Prioridad:** 🟢 MVP listo

### 4.1 — Dockerfile multi-stage
**Estado:** ⏳ Pendiente

- [ ] Separar dev/prod stages
- [ ] Optimizar tamaño de imagen final
- [ ] Multi-platform support (opcional)

**Archivo a modificar:** `Dockerfile`

---

### 4.2 — Configurar plataforma de deploy
**Estado:** ⏳ Pendiente

- [ ] Elegir: Railway, Render, Fly.io, o similar
- [ ] Configurar PostgreSQL managed
- [ ] Variables de entorno en la plataforma
- [ ] Healthcheck profundo (`/health` con DB ping)

**Opciones:**
| Plataforma | Pros | Cons |
|------------|------|------|
| Railway | Deploy automático, PostgreSQL incluido | Límite gratuito bajo |
| Render | Free tier generoso | Cold starts lentos |
| Fly.io | Multi-region | Configuración más compleja |

---

### 4.3 — Workflow CD
**Estado:** ⏳ Pendiente

- [ ] GitHub Actions para deploy automático
- [ ] Build → Test → Push → Deploy
- [ ] Notificaciones de deploy fallido

**Archivo a crear:** `.github/workflows/deploy.yml`

---

### 4.4 — Healthcheck profundo
**Estado:** ⏳ Pendiente

- [ ] Endpoint `/health` con DB ping
- [ ] Readiness vs Liveness probes separadas
- [ ] Métricas básicas (opcional)

**Archivo a modificar:** `app/main.py`

---

## Fase 5: Polish

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
| 2026-04-13 | ✅ 2.4: Logging de queries lentas de DB (threshold 1.0s, event listeners) |
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
