# Auditoría de Production-Readiness — Monolith API

> FastAPI · Clean Architecture + DDD · features Auth/Users/Todos/Notifications · SQLAlchemy/Alembic · Render
> Metodología: lectura de código real, citas `archivo:línea`. Severidad: 🔴 Crítico · 🟠 Alto · 🟡 Medio · 🔵 Bajo.
> Estado: Bloque 1 ✅ · Bloque 2 ✅ · Bloque 3 ✅ · Bloque 4 ✅ — AUDITORÍA COMPLETA

---

## 🏛️ Bloque 1 — Arquitectura y Principios

**Veredicto:** APTO con reservas. Cero críticos. Regla de dependencia respetada, dominio puro y rico, use cases limpios, DIP bien montado. La deuda está en las **fronteras entre features**.

### 🟠 Alto

**A1 — `UserModel` sin dueño claro (acoplamiento infra→infra cruzado)**
- `auth_repository.py:11-12`, `google_auth_repository.py:13-16` importan `users.infrastructure.models.UserModel` + `user_mapper` directo; `user_repository.py:12` también opera `UserModel`. La persistencia del agregado User está repartida entre `auth` y `users` sin frontera.
- **Por qué importa:** rompe la autonomía de features; un cambio en `users` rompe `auth` en silencio. Impide extraer features.
- **Fix:** `users` expone un puerto (`UserProvider`/`UserWriter` en `users/application/contracts/`); `auth` depende del contrato, no de `UserModel`.

**A2 — Invariante de creación aplicada en rehidratación (bug de lectura de TODOs vencidos)**
- `todo.py:24-35` corre `_validate_due_date` SIEMPRE en `__post_init__`; `todo_mapper.py:5-16` reconstruye vía constructor → leer un todo ya vencido lanza `ValueError` → 500 en `GET /todos`. `Notification` lo hizo bien (`notification.py:84` guarda con `if self.id is None`); `Todo` no.
- **Fix:** valida "no en el pasado" solo en un factory de creación, o replica el guard `id is None`.

### 🟡 Medio

**M1 — ISP: puertos gordos cruzando features**
- `process_reminders_use_case.py:19-29` recibe `AuthDatasource` y `TodoDatasource` completos; solo usa `get_user_by_id` y `get_todos_with_upcoming_due_date`. Acoplamiento `notifications/application → auth/todos`.
- **Fix:** puerto angosto propiedad del consumidor (`ReminderUserLookup`).

**M2 — Contrato duplicado/muerto `NotificationStore`**
- `notification_store.py:7` (Protocol) solapa `notification_datasource.py:9` (ABC); `notification_repository.py:19` implementa ambos; `NotificationStore` nunca se inyecta. `create()→save()`, `get_by_user()→find_by_user()` son alias. Dos estilos (Protocol vs ABC) en la misma feature.
- **Fix:** borrar `NotificationStore`, dejar solo `NotificationDatasource` (ABC).

**M3 — Dead code / YAGNI en notifications**
- `SetNotificationAsSentUseCase` cableado en DI (`dependencies.py:64-70`) sin endpoint que lo use; `find_pending()` (`notification_repository.py:65`) sin uso; `get_notification_repository` redundante con `get_notification_datasource`.

**M4 — `_require_user_id` duplicado x3 con semántica divergente**
- `todos/api.py:44-48` y `users/api.py:36-40` → 500; `notifications/api.py:39-43` → 401. Mismo evento, distinto código HTTP.
- **Fix:** un helper compartido, una semántica.

### 🔵 Bajo
- **B1** — DI de Google tipa concretos (`GoogleOAuthProviderImpl`, `GoogleAuthRepository`) en vez de puertos (`auth/di/dependencies.py:178-211`); los use cases sí dependen de ABCs.
- **B2** — `ProcessRemindersUseCase` no extiende `UseCase`, usa `execute(days_ahead=1)` primitivo; el endpoint devuelve `dict` crudo (`notifications/api.py:100-101`).
- **B3** — Imports dentro de métodos (`initiate_google_login.py:38`, `handle_google_callback.py:96`, `main.py:141`).

### ✅ Fortalezas
- Dominio PURO (cero framework/infra/core en `domain/` — verificado) y RICO (state machine en `Notification`, value objects, factories).
- Use cases orquestan sin tocar infra (`LoginUser`, `HandleGoogleCallback`).
- Presentation limpia (`todos/api.py` ejemplar). DIP por constructor + `Depends`.

---

## 🔒 Bloque 2 — Seguridad

**Veredicto:** NO APTO para producción hasta resolver S1 (login sin rate limit) y S2 (CSRF en OAuth). La base cripto (Argon2, rotación de refresh con detección de reuso, OTP con CSPRNG) es excelente; los huecos están en el perímetro (rate limiting, CSRF OAuth, logs).

### 🔴 Crítico

**S1 — `/login` sin rate limiting + `GlobalRateLimitMiddleware` definido pero NUNCA registrado**
- `rate_limit_global.py:13` define el middleware global, pero `main.py:53` solo registra CORS — el middleware global jamás se añade a la app (verificado por grep: un solo `add_middleware`). `/login` (`auth/presentation/api.py:88-97`), `/register` y `/refresh` no tienen ningún throttle.
- **Por qué importa:** fuerza bruta / credential stuffing / password spraying sin límite. OWASP A07 (Authentication Failures). En una API de auth esto es inaceptable.
- **Fix:** registrar el rate limiting y aplicar un límite estricto por IP+email en `/login` (p.ej. 5-10/min) y `/register`/`/refresh`. Backend durable (ver S3).

### 🟠 Alto

**S2 — CSRF en OAuth: el `state` se genera pero NUNCA se valida**
- `initiate_google_login.py:33-40` genera `state` con `secrets.token_urlsafe(32)`, pero `handle_google_callback.py:42-82` recibe `params.state` y **no lo referencia jamás** — no hay persistencia ni comparación.
- **Por qué importa:** sin validación de `state`, el callback OAuth es vulnerable a CSRF (login forzado / vinculación de cuenta atacante). OWASP A01.
- **Fix:** persistir el `state` emitido (cookie firmada httponly o store server-side) y compararlo en el callback; rechazar si no coincide.

**S3 — Rate limiter en memoria: no durable, no multi-worker**
- `in_memory_rate_limiter.py:9` + `di/dependencies.py:45` (`_rate_limiter = InMemoryRateLimiter()`, singleton por proceso). El propio `rate_limit_global.py:18` lo admite ("for production use Redis").
- **Por qué importa:** el estado se pierde en cada restart (Render free hace spin-down) y diverge con >1 worker/instancia. El throttle de OTP (único activo) es frágil.
- **Fix:** backend compartido (Redis) para todos los rate limits.

**S4 — Datos sensibles en logs: el handler de validación loguea el `input` crudo**
- `error_handling.py:28` → `logger.warning(f"Validation error: {exc.errors()}")`. En Pydantic v2, `errors()` incluye la clave `input` con el valor enviado → un registro/cambio de password con password débil deja la **password en texto plano** en logs (retención 30-90 días, `logger_config.py:36-68`).
- **Por qué importa:** OWASP A09 (Logging Failures). Secreto en claro persistido.
- **Fix:** sanitizar — loguear solo `loc`+`type`+`msg`, nunca `input`; o redactar campos sensibles.

### 🟡 Medio

**S5 — OTP almacenado como SHA-256 sin sal**
- `otp_repository.py:133` `hashlib.sha256(code).hexdigest()`. Espacio de 10^6 + hash rápido sin sal → rainbow table trivial si la BD se filtra.
- **Mitigado por:** TTL 10 min + un solo uso. **Fix:** HMAC-SHA256 con secreto de servidor, o sal por fila.

**S6 — Respuestas 500 filtran mensajes internos vía `str(exc)`**
- `error_handling.py:94` (`DatabaseError`) y `:106` (`InternalServerError`) devuelven `"detail": str(exc)`. No son stacktraces (los strings son de la app), pero exponen detalle interno. El handler genérico (`:80`) sí oculta bien.
- **Fix:** detalle genérico en prod; el específico solo a logs.

**S7 — Faltan headers de seguridad (HSTS, CSP)**
- `security_headers.py:3-8` tiene `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, pero **no** `Strict-Transport-Security` ni `Content-Security-Policy`. `X-XSS-Protection` está deprecado.
- **Fix:** añadir HSTS (`max-age` largo, `includeSubDomains`) y una CSP mínima; quitar X-XSS-Protection.

**S8 — `verify_password` no captura `InvalidHash`**
- `password_manager_impl.py:17-22` solo atrapa `VerifyMismatchError`; un hash malformado en BD lanza `argon2.exceptions.InvalidHash` → 500 en vez de fallo de auth limpio.
- **Fix:** capturar también `InvalidHash` (y `VerificationError`) → `return False`.

### 🔵 Bajo
- **S9** — Comparación no constante del token interno: `notifications/api.py:97` `token != env_config.internal_api_key` → timing side-channel. Usar `secrets.compare_digest`.
- **S10** — JWT sin `iss`/`aud` ni leeway (`jwt_token_manager.py`). OK para monolito; endurecer si crece.
- **S11** — Enumeración de cuentas en `/register` (409 distingue emails existentes). Login es genérico (bien).
- **S12** — `CORS_ALLOWED_ORIGINS` no está en `render.yaml` → prod cae al default `localhost:3000` (`main.py:23`); seguro pero probablemente mal configurado para el frontend real. `/docs` y `/openapi.json` expuestos (intencional para portfolio).

### ✅ Fortalezas (sólidas)
- **Argon2** para passwords (`password_manager_impl.py`) — estándar de oro.
- **Rotación de refresh con detección de reuso** (`refresh_access_token_use_case.py:26-43`): si reusan un token revocado → `revoke_all_for_user`. Textbook.
- **Validación de tipo de token** (`jwt_token_manager.py:44-55`, `get_current_user_use_case.py:16`): un refresh no autentica.
- **OTP**: `secrets.randbelow` (CSPRNG), un solo uso, TTL 10 min, invalida previos, almacenado hasheado; verify con rate limit cuya ventana calza con el TTL (5/10min) → brute-force inviable.
- **Cero SQL injection**: todo ORM parametrizado; sin interpolación de strings.
- **Input validation fuerte** (`auth_requests.py`): complejidad de password, `EmailStr`+VO, regex OTP `^\d{6}$`, max lengths, strip.
- **Secrets** vía env con `sync: false` (`render.yaml`); sin hardcodes; `.env` y `logs` gitignoreados.
- **Docker** con usuario no-root; `diagnose=False` en loguru (no vuelca variables); change-password revoca todas las sesiones; link-google re-verifica password.

### Lista priorizada Bloque 2
| # | Sev | Hallazgo | Esfuerzo |
|---|-----|----------|----------|
| S1 | 🔴 | `/login` sin rate limit; middleware global no registrado | Medio |
| S2 | 🟠 | CSRF OAuth: `state` no validado | Medio |
| S4 | 🟠 | Password en texto plano en logs (`exc.errors()`) | Bajo |
| S3 | 🟠 | Rate limiter en memoria (no durable/multi-worker) | Medio (Redis) |
| S5 | 🟡 | OTP SHA-256 sin sal | Bajo |
| S6 | 🟡 | 500 filtran `str(exc)` | Bajo |
| S7 | 🟡 | Faltan HSTS/CSP | Bajo |
| S8 | 🟡 | `verify_password` no captura `InvalidHash` | Trivial |
| S9-S12 | 🔵 | timing token interno, JWT iss/aud, enum register, CORS prod | Bajo |

---

## 🧪 Bloque 3 — Testing y Manejo de Errores

**Veredicto:** SÓLIDO. Pirámide sana (≈143 unit / 65 integration / 7 e2e = 66/30/3 %, 215 tests), mocks de **puertos** (no implementaciones), paths de error cubiertos, e2e con escenarios de seguridad reales, y gate de coverage 85% en CI. Los huecos son de calidad fina, no estructurales — salvo dos que importan: tests solo en SQLite (prod es Postgres) y la rama de detección de reuso sin cubrir.

### 🟠 Alto

**T1 — Los tests corren solo en SQLite; producción es PostgreSQL; las migraciones Alembic NUNCA se ejecutan**
- `conftest.py:19` crea `sqlite+pysqlite:///:memory:` y arma el esquema con `metadata.create_all` (`:26`), saltándose Alembic. El CI (`tests.yml:64-71`) escribe un `.env` con Postgres pero **no levanta servicio Postgres** y los tests usan el fixture SQLite → la BD de prod nunca se ejercita. Verificado: cero tests tocan `postgresql/psycopg`.
- **Por qué importa:** SQLite ≠ Postgres (constraints, `IntegrityError`, tipos, `server_default text("FALSE")`, aislamiento). El mapeo `IntegrityError→ConflictError` puede comportarse distinto. Y como las migraciones no se corren en CI, **el drift entre modelos y migraciones queda invisible** hasta el deploy (donde se aplican en `main.py:27-43`).
- **Fix:** servicio `postgres` en CI (services container) + un set de tests de repositorio/e2e contra Postgres real; correr `alembic upgrade head` en CI y validar que el esquema resultante == modelos.

**T2 — La detección de reuso (la feature de seguridad clave) no está cubierta a nivel de use case**
- `refresh_access_token_use_case.py:26-28` (si `is_revoked` → `revoke_all_for_user` + `raise`) nunca se ejercita: `test_auth_use_cases.py:193` fija `is_revoked=False`; no hay e2e que reuse un refresh token. El repo testea `is_revoked`/`revoke_all_for_user` por separado, pero la ORQUESTACIÓN del reuso no.
- **Por qué importa:** es justo lo que el coverage de línea al 85% esconde — la línea se "cubre" indirectamente pero la RAMA crítica no. Si alguien rompe esa lógica, ningún test lo detecta.
- **Fix:** test de use case con `is_revoked=True` que asserte `revoke_all_for_user` + `UnauthorizedError`, y un e2e que use el mismo refresh dos veces.

### 🟡 Medio

**T3 — Coverage es solo de LÍNEA, no de rama**
- `tests.yml:72` usa `--cov-fail-under=85` sin `--cov-branch` ni `[tool.coverage.run] branch=true`. El gate del 85% es line coverage.
- **Fix:** activar `--cov-branch`; recalibrar el umbral (la rama suele bajar el número y revela huecos como T2).

**T4 — `ValueError → 400` global mezcla validación de dominio con bugs internos**
- `error_handling.py:171` mapea CUALQUIER `ValueError` a 400 con `str(exc)`. El dominio lanza `ValueError` para invariantes (correcto → 400), pero un bug interno que lance `ValueError` (p.ej. A2: leer un todo vencido) se disfraza de 400 con mensaje interno hacia el cliente.
- **Fix:** que el dominio lance una excepción específica (`DomainValidationError(AppError)`); reservar `ValueError` genérico para 500.

**T5 — Cero tests de concurrencia / race conditions**
- Verificado: ningún test usa threading/async-gather. Sin cobertura para: doble refresh concurrente (doble emisión), doble consumo de OTP, o el `Lock` del rate limiter bajo hilos.
- **Fix:** tests con `ThreadPoolExecutor` para los caminos con estado compartido.

### 🔵 Bajo
- **T6** — `NotificationRepository` (SQL) y los endpoints de notifications no tienen tests (solo dominio + use cases). Refuerza eliminar la feature.
- **T7** — Alias de excepciones duplicados (`exceptions.py:37-57`: `DatabaseException` vs `DatabaseError`, etc.) usados inconsistentemente (notifications usa `DatabaseException`, el resto `DatabaseError`).
- **T8** — Cosmético: docstrings autogenerados en español raro, comentarios `# Tipo de test:` dispersos (uno vacío en `test_auth_use_cases.py:83-84`), uso bajo de `parametrize` (5 en 215 tests).

### ✅ Fortalezas
- **Pirámide sana** 66/30/3 — base unit amplia, integración media, e2e fino. Nada de "demasiados e2e lentos".
- **Mocks correctos**: `Mock(spec=AuthDatasource)` etc. — mockean **contratos ABC**, no concretos; `spec=` atrapa drift de firma.
- **Paths de error cubiertos**: email inválido, user not found, password incorrecta, subject faltante (`test_auth_use_cases.py`).
- **E2E con seguridad real** (`test_auth_users_todos_e2e.py`): ownership cross-user (404), OTP change-password + rechazo de reuso, rate limit 429, OAuth conflict 409, token inválido 401. 7 e2e significativos, no redundantes.
- **Manejo de errores**: jerarquía limpia `AppError` → tipos; handlers registrados UNA vez (`main.py:49`); catch-all `Exception` al final; 500 enmascarado; correlación por `request_id`; cubierto por `test_error_handling.py` (9 tests).

### Lista priorizada Bloque 3
| # | Sev | Hallazgo | Esfuerzo |
|---|-----|----------|----------|
| T1 | 🟠 | Tests solo SQLite; Postgres y migraciones sin ejercitar | Medio |
| T2 | 🟠 | Rama de detección de reuso sin test | Bajo |
| T3 | 🟡 | Coverage solo de línea (sin `--cov-branch`) | Trivial |
| T4 | 🟡 | `ValueError→400` global esconde bugs internos | Bajo |
| T5 | 🟡 | Sin tests de concurrencia/race | Medio |
| T6-T8 | 🔵 | notifications sin tests; alias duplicados; cosmético | Bajo |

---

## ⚙️ Bloque 4 — Operación (Performance · Observabilidad · API Design · DevOps)

**Veredicto:** NO APTO para producción — y no por lo de siempre. Encontré un **drift de esquema crítico** que rompe la feature central (todos) en producción y que tus tests no detectan porque corren en SQLite. La base operativa (índices, logs estructurados, correlation IDs, CI con gates) es buena; el problema es el gap entre el esquema testeado y el desplegado.

### 🔴 Crítico

**O1 — Drift de esquema: `todos.due_date` existe en el modelo y el código, pero NINGUNA migración la crea**
- `todo_model.py:21` declara `due_date`; el código lo usa (create/update/reminders). Verificado: cero migraciones Alembic mencionan `due_date`. La migración real de todos (`c514730db220`) crea la tabla SIN esa columna.
- **Por qué importa:** los tests pasan porque `conftest.py:26` usa `metadata.create_all` (crea la columna desde el modelo en SQLite). Pero producción usa Postgres + Alembic (`main.py:27-43`) → la columna NO existe → `POST /v1/todos` y `GET /v1/todos` con `due_date` lanzan `UndefinedColumn` → **la feature central está rota en prod.** Es el T1 materializado.
- **Fix:** generar `alembic revision` que haga `op.add_column("todos", due_date)`; y cerrar el agujero de proceso (T1: tests contra Postgres + `alembic upgrade head` en CI con verificación de drift modelo↔migración, p.ej. `alembic check`).

### 🟠 Alto

**O2 — La migración en startup traga el error y arranca igual**
- `main.py:36-42`: `try: command.upgrade(...) except Exception as e: logger.error(...)` y luego `yield`. Si la migración falla, la app **igual sirve tráfico** contra un esquema roto/desactualizado.
- **Por qué importa:** en Render free no hay shell ni migraciones manuales (restricción real del usuario), así que este startup es el ÚNICO camino. Tragar el error = deploy roto silencioso. Combinado con O1, es exactamente lo que pasaría.
- **Fix:** fail-fast — si la migración falla, no hacer `yield` (que el proceso muera y Render reintente/avise) o marcar readiness en rojo.

**O3 — `/health` devuelve 200 aunque la DB esté caída**
- `main.py:138-151` retorna `{"status":"healthy","database":"unhealthy"}` con **status 200** cuando la DB falla. `render.yaml:8` usa `healthCheckPath: /health`.
- **Por qué importa:** Render y cualquier readiness probe creen que está sano aunque la DB esté muerta. No hay distinción liveness/readiness por status code.
- **Fix:** `/health` (readiness) → 503 si la DB no responde; dejar `/` como liveness puro.

### 🟡 Medio

**O4 — Sin paginación en listados + `GET /v1/users` expone PII de todos**
- `user_repository.py:24` (`.all()`) y `get_todos` retornan TODAS las filas, sin `limit/offset`. Además `users/presentation/api.py:50-57`: cualquier usuario autenticado lista a TODOS los usuarios (name, email, birthdate) — sin rol/admin.
- **Fix:** paginación (`limit/offset` o cursor) en todos los listados; restringir `/users` a admin o quitarlo.

**O5 — Connection pool sin configurar (frágil en Render free)**
- `database.py:32,42` `create_engine(...)` sin `pool_pre_ping`, `pool_recycle`, `pool_size`. Render free Postgres corta conexiones idle → sin `pool_pre_ping` salen errores de conexión muerta; el pool default puede pasarse del límite de conexiones del free tier.
- **Fix:** `pool_pre_ping=True`, `pool_recycle=300`, `pool_size` chico acorde a Render free.

**O6 — Códigos OTP filtrados por `print()` en `ConsoleEmailSender`**
- `console_email_sender.py:8,11` hace `print(f"[OTP] ... code={code}")`. Si en prod faltan las keys de Resend, `get_email_sender` cae al console sender → **OTP en stdout** (capturado por logs de Render). Además usa `print`, no el logger estructurado.
- **Fix:** nunca loguear el código; usar logger y redactar; garantizar Resend en prod o fallar.

**O7 — Versionado de API inconsistente**
- `/auth/v1/...` (auth con `prefix="/auth"`) vs `/v1/users`, `/v1/todos` vs notifications montado en `/v1` con path vacío (`GET /v1`). El segmento de versión no está colocado de forma uniforme.
- **Fix:** unificar (p.ej. todo bajo `/api/v1/<feature>`).

**O12 — Proxy headers no manejados → IP de cliente incorrecta detrás de Render (CRUCIAL para rate limiting)**
- `rate_limit_global.py:39` usa `request.client.host` para la key por IP, pero uvicorn se lanza SIN `--proxy-headers` (`render.yaml:7`, `Dockerfile:24`). Detrás del proxy de Render, `request.client.host` = IP del proxy, no del cliente → el rate limiting por IP agrupa a TODOS los usuarios bajo una IP (inútil o bloqueo masivo) y los logs registran la IP equivocada.
- **Fix:** `uvicorn --proxy-headers --forwarded-allow-ips='*'` (o rango de Render) y derivar IP de `X-Forwarded-For`. Ligado a S1/S3.

### 🔵 Bajo
- **O8** — `DELETE` retorna 200+body en vez de 204; validación partida entre 400 (`RequestValidationError`) y 422 (`ValidationError` de dominio).
- **O9** — El **Dockerfile NO lo usa Render** (`render.yaml:4` `runtime: python` + `buildCommand: pip install`). Artefacto muerto para deploy (sirve local); además es single-stage y el CI nunca buildea la imagen.
- **O10** — Migración vacía/ruido `368a38931a3f` ("create todos table" que no hace nada) — historial confuso.
- **O11** — N+1 en `process_reminders` (`get_user_by_id` por cada todo) — pero la feature se va a eliminar.

### ✅ Fortalezas
- **Índices** en todos los filtros frecuentes: `email`/`google_id` unique+index, `user_id` en todos/refresh_tokens/otps, `purpose` en otps.
- **Logs estructurados JSON** (`logger_config.py` sink `.jsonl` con `serialize=True`) + rotación/retención; **correlation IDs** propagados a logs y header `X-Request-ID` (`request_context.py`).
- **CI con gates**: ruff + black + mypy + pytest + coverage 85%.
- **Migraciones lineales** (un solo head, una base, sin ramas) y todas con `downgrade`.
- **Migrar en startup es el patrón correcto** dada la restricción de Render free (solo falta el fail-fast de O2).
- `.dockerignore` presente y correcto; usuario non-root; imagen slim; verbos HTTP correctos (PATCH para read); OpenAPI con BearerAuth y rutas públicas marcadas.

### Lista priorizada Bloque 4
| # | Sev | Hallazgo | Esfuerzo |
|---|-----|----------|----------|
| O1 | 🔴 | Drift: `todos.due_date` sin migración (rompe prod) | Bajo (migración) |
| O2 | 🟠 | Migración en startup traga error y arranca igual | Bajo |
| O3 | 🟠 | `/health` siempre 200 aunque DB caída | Trivial |
| O4 | 🟡 | Sin paginación + `/users` expone PII | Medio |
| O5 | 🟡 | Connection pool sin `pool_pre_ping`/recycle | Trivial |
| O6 | 🟡 | OTP en logs vía `print` (console sender) | Bajo |
| O7 | 🟡 | Versionado de API inconsistente | Medio |
| O8-O11 | 🔵 | 204, Dockerfile muerto, migración ruido, N+1 | Bajo |

---

## 🎯 Resumen ejecutivo global (4 bloques)

**Estado general:** Arquitectura y testing de nivel profesional sobre una base sólida; pero **NO desplegable hoy** por bugs de producción concretos (O1, S1, S2). La buena noticia: casi todo es acotado, no estructural.

### Top críticos a resolver antes de producción
| Prioridad | ID | Bloque | Qué | Por qué |
|-----------|----|--------|-----|---------|
| 1 | O1 | Operación | `todos.due_date` sin migración | Rompe la feature central en prod |
| 2 | S1 | Seguridad | `/login` sin rate limit (middleware global no registrado) | Fuerza bruta sin límite |
| 3 | S2 | Seguridad | CSRF OAuth: `state` no validado | Login/link forzado |
| 4 | O2 | Operación | Migración startup traga error | Deploy roto silencioso (Render free) |
| 5 | A2 | Arquitectura | Invariante en rehidratación de `Todo` | 500 al leer todos vencidos |
| 6 | S4 | Seguridad | Password en texto plano en logs | Secreto persistido |
| 7 | T1/T2 | Testing | Tests en SQLite (no Postgres), reuso sin test | Esconde O1 y regresiones de seguridad |

### Temas transversales (la causa raíz se repite)
1. **Fronteras entre features** (A1, M1, M2, M3) → introducir puertos; eliminar `notifications`.
2. **Gap test↔producción** (T1 → O1) → Postgres en CI + `alembic check`. Este es el patrón más peligroso: tu red de seguridad (tests) no cubre lo que se despliega.
3. **Rate limiting incompleto y no durable** (S1, S3) → registrar + Redis.
4. **Fugas a logs** (S4, O6) → sanitizar el logging.

### Lo que está MUY bien (no tocar)
Dominio puro y rico (DDD real), use cases limpios, DIP por constructor, Argon2, rotación de refresh con detección de reuso, OTP con CSPRNG, cero SQLi, input validation fuerte, índices correctos, logs estructurados con correlation IDs, CI con gates de calidad. La fundación es de las buenas — los problemas son de borde, no de cimientos.
