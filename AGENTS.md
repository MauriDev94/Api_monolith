# AGENTS.md

Guía de coordinación del sistema de agentes para el proyecto monolito modular FastAPI con Clean Architecture + DDD.

---

## Sistema de Agentes

Este proyecto usa **3 agentes especializados**. Cada agente tiene responsabilidades exclusivas y no las comparte.

```
.github/agents/
├── Backend-architect.agent.md     # Diseño y revisión arquitectónica
├── Backend-implementer.agent.md   # Implementación de features por capas
└── Backend-test-engineer.agent.md # Diseño e implementación de tests

skills/
├── clean-architecture-ddd.md      # Referencia arquitectónica completa
├── fastapi-api-patterns.md        # Patrones de presentación y DI
└── python-testing-patterns.md     # Patrones de testing con pytest
```

---

## Cuándo usar cada agente

| Situación | Agente |
|-----------|--------|
| Nueva feature desde cero | Arquitecto → Implementador → Test Engineer |
| Refactor de código existente | Arquitecto primero, luego Implementador |
| Solo agregar un endpoint | Implementador |
| Solo agregar tests | Test Engineer |
| Detectar violaciones arquitectónicas | Arquitecto |
| Revisar PR completo | Arquitecto + Test Engineer |
| Bug en lógica de dominio | Implementador |
| Mejorar cobertura de tests | Test Engineer |

---

## Flujo de coordinación entre agentes

### Feature nueva
```
1. Arquitecto   → diseña dominio, define capas afectadas, valida approach
2. Implementador → implementa capa por capa: domain → application → infrastructure → presentation → di
3. Test Engineer → escribe tests por prioridad: unit → integration → e2e
```

### Refactor
```
1. Arquitecto   → identifica violaciones, propone cambio mínimo seguro
2. Test Engineer → crea cobertura del comportamiento actual ANTES del cambio
3. Implementador → aplica el refactor
4. Test Engineer → valida regresión completa
```

### Revisión de PR
```
1. Arquitecto   → verifica dirección de dependencias y ubicación de lógica
2. Test Engineer → verifica cobertura y calidad de tests
```

---

## Estructura del proyecto

```
app/
├── main.py
├── common/
│   ├── use_case.py
│   └── use_case_no_params.py
├── core/
│   ├── config/
│   │   └── env_config.py
│   ├── data/source/local/
│   │   ├── database.py
│   │   ├── sql_alchemy_base.py
│   │   └── alembic/
│   ├── exceptions/
│   │   ├── exceptions.py
│   │   └── error_handling.py
│   ├── middleware/
│   │   └── request_context.py
│   ├── providers/
│   │   └── db.py
│   └── router/
│       └── router.py
└── features/
    ├── auth/
    ├── todos/
    └── users/
        ├── domain/
        │   ├── entities/
        │   └── value_objects/
        ├── application/
        │   ├── contracts/
        │   ├── dto/
        │   └── usecases/
        ├── infrastructure/
        │   ├── models/
        │   ├── mappers/
        │   └── repositories/
        ├── presentation/
        │   ├── api.py
        │   ├── schemas/
        │   └── mappers/
        └── di/
            └── dependencies.py
```

---

## Estructura de tests

```
tests/
├── conftest.py                         # Fixtures globales (DB, client)
├── unit/
│   └── features/
│       ├── users/
│       │   ├── domain/                 # Entidades y Value Objects — sin mocks
│       │   └── application/           # Use cases — mock de contratos
│       ├── todos/
│       └── auth/
├── integration/
│   └── features/
│       └── users/
│           └── infrastructure/        # Repositorios contra DB de test
└── e2e/
    └── features/
        └── users/                     # Contrato HTTP completo
```

---

## Dirección de dependencias (estricta)

```
presentation → application → domain
infrastructure → application + domain
domain → nada
```

Violaciones bloqueantes — ningún agente puede generar código que las contenga:
- `domain` importa `fastapi`, `sqlalchemy`, `pydantic` o cualquier módulo de `infrastructure`
- `application` importa desde `infrastructure` o `presentation`
- `presentation` accede a repositorios o modelos ORM directamente
- Un use case instancia un repositorio concreto en lugar de recibir el contrato

---

## Naming conventions

| Elemento | Patrón | Ejemplo |
|----------|--------|---------|
| Entidad | PascalCase | `User`, `Todo` |
| Value Object | PascalCase | `Email`, `HashedPassword` |
| Use Case | `VerbNombreUseCase` | `CreateTodoUseCase` |
| Params DTO | `VerbNombreParams` | `CreateTodoParams` |
| Result DTO | `NombreResult` | `UserResult`, `TokenPairResult` |
| Contrato | `NombreDatasource` | `UserDatasource`, `TodoDatasource` |
| Repositorio | `NombreRepository` | `UserRepository` |
| Mapper infra | `NombreMapper` en `infrastructure/mappers/` | `UserMapper` |
| Mapper presentación | `NombrePresentationMapper` en `presentation/mappers/` | `UserPresentationMapper` |
| Schema request | `VerbNombreRequest` | `CreateUserRequest` |
| Schema response | `NombreResponse` | `UserResponse` |
| Excepción dominio | `NombreError` | `UserNotFoundError` |
| Test | `test_<behavior>_when_<condition>` | `test_email_raises_when_domain_has_numbers` |

---

## Jerarquía de excepciones

```python
# core/exceptions/exceptions.py
AppError          # base — todos los errores de dominio/aplicación heredan de aquí
├── NotFoundError       # 404
├── ConflictError       # 409
├── UnauthorizedError   # 401
├── ForbiddenError      # 403
└── ValidationError     # 422
```

- Las excepciones se lanzan en `domain` o `application`
- Se capturan y mapean a HTTP en `core/exceptions/error_handling.py`
- Los endpoints no hacen `try/except` de lógica de negocio

---

## Clean Code — reglas base

- Funciones ≤ 20 líneas
- Una función = una responsabilidad
- Nombres explícitos y descriptivos (sin abreviaciones)
- Type hints en todas las funciones y métodos
- Sin comentarios redundantes — el código debe ser autoexplicativo
- DRY: no duplicar lógica entre capas

---

## Prohibiciones absolutas

- Lógica de negocio en `presentation` o `infrastructure`
- Imports de `fastapi` o `sqlalchemy` en `domain`
- Instanciar repositorios concretos fuera de `di/dependencies.py`
- Exponer ORM models (`infrastructure/models/`) fuera de `infrastructure`
- Exponer entidades de dominio directamente como response schemas
- God objects (clases con más de una responsabilidad)
- DTOs sin tipado explícito

---

## Skills de referencia

Cada agente debe leer el skill correspondiente antes de actuar:

| Agente | Skills obligatorios |
|--------|---------------------|
| Arquitecto | `clean-architecture-ddd.md` |
| Implementador | `clean-architecture-ddd.md` + `fastapi-api-patterns.md` |
| Test Engineer | `python-testing-patterns.md` + `clean-architecture-ddd.md` |
