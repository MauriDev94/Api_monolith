# SDD Proposal — Phase 10: Google SSO Login

**Date:** 2026-05-17
**Status:** Completed
**Priority:** 🟢 Completa

---

## Context

El proyecto ya tiene auth completo con email/password + OTP. Esta fase agrega
login con Google OAuth2 como método alternativo de autenticación, sin romper
el flujo existente.

---

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | `password_hash` nullable en `User` | Usuarios OAuth no tienen contraseña. Nullable es honesto y no requiere flag redundante. |
| 2 | `google_id` columna en `users` | Un solo provider por ahora. Si se agrega GitHub u otro, se migra a `user_identities`. |
| 3 | `GoogleAuthDatasource` separado | `AuthDatasource` tiene responsabilidad clara. No mezclar contratos. |
| 4 | Mock del token de Google en E2E | El flujo queda cubierto en CI sin depender de Google real. |
| 5 | Usuario Google puede setear contraseña después | `password_hash` nullable + endpoint existente `/auth/v1/change-password` lo resuelve solo. |

---

## API Contract

### Nuevos endpoints
GET /auth/v1/google
→ 302 redirect a Google OAuth consent screen

> **Nota de desvío (shipping):** la implementación final (#106) retornó
> `200 + { authorization_url }` (JSON), no `302 redirect`. La intención
> original de delegar la navegación al frontend para mantener el backend
> sin estado se materializó así. Ver `docs/ARCHITECTURE.md` §8.1 punto 6
> y `app/features/auth/presentation/api.py` (`GET /auth/v1/google`).

GET /auth/v1/google/callback?code=...&state=...
→ 200 { access_token, refresh_token, token_type }
→ 409 si el email ya existe con password (cuenta duplicada)

### Endpoints existentes sin cambios

Todos los endpoints actuales mantienen su contrato. El cambio en
`password_hash` es interno — ningún response schema lo expone.

---

## Layer Changes

### Domain

**`app/features/users/domain/entities/user.py`**
- `password_hash: str` → `password_hash: str | None`
- `__post_init__`: omitir validación de `password_hash` cuando es `None`
- `change_password_hash(new_hash: str) -> None`: nuevo método de comportamiento

**No hay nuevos Value Objects.**

### Application

**`app/features/auth/application/contracts/google_auth_datasource.py`** (nuevo)
```python
class GoogleAuthDatasource(ABC):
    def get_user_by_google_id(self, google_id: str) -> User | None: ...
    def get_user_by_email(self, email: str) -> User | None: ...
    def create_google_user(self, params: CreateGoogleUserParams) -> User: ...
    def link_google_id(self, user_id: str, google_id: str) -> None: ...
```

**`app/features/auth/application/contracts/google_oauth_provider.py`** (nuevo)
```python
class GoogleOAuthProvider(ABC):
    def get_authorization_url(self, state: str) -> str: ...
    def exchange_code(self, code: str) -> GoogleTokenData: ...
    def get_user_info(self, access_token: str) -> GoogleUserInfo: ...
```

**`app/features/auth/application/dto/create_google_user_params.py`** (nuevo)
```python
@dataclass(slots=True)
class CreateGoogleUserParams:
    google_id: str
    email: str
    name: str
    lastname: str
```

**`app/features/auth/application/dto/google_user_info.py`** (nuevo)
```python
@dataclass(slots=True)
class GoogleUserInfo:
    google_id: str
    email: str
    name: str
    lastname: str
```

**`app/features/auth/application/dto/google_token_data.py`** (nuevo)
```python
@dataclass(slots=True)
class GoogleTokenData:
    access_token: str
    id_token: str
```

**`app/features/auth/application/usecases/google_login_use_case.py`** (nuevo)

Flujo:
1. Exchange `code` → `GoogleTokenData`
2. Get user info → `GoogleUserInfo`
3. Buscar por `google_id` → si existe, issue tokens
4. Buscar por `email` → si existe con password, raise `ConflictError`
5. Si no existe → crear usuario, issue tokens

### Infrastructure

**`app/features/users/infrastructure/models/user_model.py`**
- Agregar columna `google_id: Mapped[str | None]` con `unique=True, nullable=True, index=True`

**`app/features/auth/infrastructure/repositories/auth_repository.py`**
- `password_hash` nullable en `register_user`

**`app/features/auth/infrastructure/repositories/google_auth_repository.py`** (nuevo)
- Implementa `GoogleAuthDatasource`
- `create_google_user`: inserta con `password_hash=None`, `google_id` poblado

**`app/features/auth/infrastructure/providers/google_oauth_provider_impl.py`** (nuevo)
- Implementa `GoogleOAuthProvider`
- Usa `httpx` (ya en requirements) para llamar a Google APIs
- URLs: `https://accounts.google.com/o/oauth2/v2/auth`, `https://oauth2.googleapis.com/token`, `https://www.googleapis.com/oauth2/v3/userinfo`

**`app/features/auth/infrastructure/providers/stub_google_oauth_provider.py`** (nuevo)
- Implementa `GoogleOAuthProvider` con datos hardcodeados
- Usado exclusivamente en tests

### Presentation

**`app/features/auth/presentation/api.py`**
```python
GET /auth/v1/google         → redirect a Google
GET /auth/v1/google/callback → ejecuta GoogleLoginUseCase, retorna tokens
```

### DI

**`app/features/auth/di/dependencies.py`**
- `get_google_oauth_provider()` → `GoogleOAuthProviderImpl` (config de env)
- `get_google_auth_repository()` → `GoogleAuthRepository`
- `get_google_login_use_case()` → `GoogleLoginUseCase`

### Config

**`app/core/config/env_config.py`**
- `google_client_id: str | None = None`
- `google_client_secret: str | None = None`
- `google_redirect_uri: str | None = None`

**`.env.example`**
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/v1/google/callback

### Migration
alembic revision --autogenerate -m "add google_id to users"
- `ALTER TABLE users ADD COLUMN google_id VARCHAR(255) UNIQUE`
- `ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL`

---

## Test Plan

### Unit tests

| Test | Archivo |
|------|---------|
| `GoogleLoginUseCase` — usuario nuevo → crea y retorna tokens | `test_google_login_use_case.py` |
| `GoogleLoginUseCase` — `google_id` existente → retorna tokens | idem |
| `GoogleLoginUseCase` — email existe con password → `ConflictError` | idem |
| `User` — `password_hash=None` válido | `test_user_entity.py` |
| `User` — `change_password_hash` muta correctamente | idem |

### Integration tests

| Test | Archivo |
|------|---------|
| `GoogleAuthRepository.create_google_user` persiste con `google_id` | `test_google_auth_repository.py` |
| `GoogleAuthRepository.get_user_by_google_id` retorna usuario | idem |
| `GoogleAuthRepository.link_google_id` asocia id a usuario existente | idem |

### E2E tests

| Test | Archivo |
|------|---------|
| Callback con `StubGoogleOAuthProvider` → 200 + tokens | `test_auth_users_todos_e2e.py` |
| Callback con email que ya tiene password → 409 | idem |
| Segundo login con mismo google_id → mismo user_id en tokens | idem |

---

### 10.9 — Presentation: Link Google Account
**Estado:** ⏳ Pendiente

- [ ] `POST /auth/v1/link-google` → endpoint para vincular cuenta existente
- [ ] Requiere: usuario logueado (cookie de sesión) + password en body
- [ ] Flujo: verificar password → link `google_id` al usuario actual
- [ ] Unit + integration tests
- [ ] Acceptance: usuario con password puede vincular su cuenta Google

### Testing Mode
**Postman-only** — Solo backend. No se crea frontend. El flujo OAuth se prueba
abriendo la redirect URL en el browser, capturando el callback response en Postman.

---

## Acceptance Criteria (DoD)

- [ ] `User.password_hash` acepta `None` sin romper tests existentes
- [ ] `GET /auth/v1/google` redirige a Google
- [ ] `GET /auth/v1/google/callback` con code válido retorna tokens
- [ ] Email ya registrado con password → 409
- [ ] Segundo login con mismo Google account → mismo user
- [ ] `POST /auth/v1/link-google` → usuario logueado puede vincular cuenta Google
- [ ] Tests existentes (195+) siguen en verde
- [ ] Coverage >= 90% en `google_login_use_case.py`
- [ ] Variables de entorno documentadas en `.env.example`
