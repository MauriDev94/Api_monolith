# Fase 7.1 — Audit técnico Notifications (baseline para refactor)

## 1) Auditoría por capa (estado actual)

### Domain
- `app/features/notifications/domain/entities/notification.py` define entidad y estados.
- Gap: faltan invariantes más estrictas de transición de estado para evitar mutaciones inválidas.

### Application
- `app/features/notifications/application/usecases/process_reminders_use_case.py` mezcla lógica de aplicación con detalles de infraestructura:
  - importa `TodoModel` (ORM)
  - importa `NotificationRepository` (infra)
  - abre sesión DB con `get_db_session` dentro del use case
- Impacto: acoplamiento alto, baja testeabilidad unitaria.

### Infrastructure
- `app/features/notifications/infrastructure/repositories/notification_repository.py` cumple persistencia base.
- Gap: errores HTTP/negocio se resuelven más arriba de forma inconsistente (falta contrato de errores de aplicación para ownership/not found).

### Presentation
- `app/features/notifications/presentation/api.py` consume repositorio directo (no use cases).
- `app/features/notifications/presentation/api_internal.py` expone trigger de reminders sin pasar por capa de casos de uso desacoplada.
- Impacto: rompe dirección ideal de dependencias (`presentation -> application -> domain`).

### DI
- `app/features/notifications/di/dependencies.py` solo provee repositorio.
- Gap: falta wiring de use cases y puertos de query/orquestación.

## 2) Duplicaciones y acoplamientos detectados

1. Acoplamiento Application→Infrastructure:
   - `process_reminders_use_case.py` usa ORM + repositorio concreto.
2. Acoplamiento Presentation→Infrastructure:
   - `api.py` depende de `NotificationRepository` concreto.
3. Ownership/errores en presentation:
   - validación de ownership en endpoint en vez de encapsular en caso de uso.
4. Falta de suite dedicada:
   - no se detectaron tests de notifications en `tests/features/notifications/**`.

## 3) Matriz de contratos API no rompibles (opción B)

## Contratos v1 (compatibilidad temporal)
- Mantener operativos:
  - `GET /notifications`
  - `PATCH /notifications/{notification_id}/read`
- Mantener semántica HTTP para consumidores actuales:
  - 200 éxito, 404 no encontrado, 403 ownership inválido.
- Marcar deprecación con documentación y ventana de migración.

## Contratos v2 (versionado)
- Publicar (target):
  - `GET /notifications/v2` (o `/v2/notifications`, según decisión final de routing)
  - `PATCH /notifications/v2/{notification_id}/read` (o equivalente `/v2`)
- Cambios permitidos en v2:
  - payload/response más explícito
  - errores de dominio homogéneos mapeados por handler global
  - metadatos opcionales (paginación, trace ids, etc.)

## Reglas de compatibilidad
- No borrar v1 en la fase 7.
- V1 y v2 conviven durante migración.
- Documentar deprecación en OpenAPI/README antes de retirada.

## 4) Criterios de aceptación técnicos por capa (DoD 7.1 → input de 7.2)

- Domain:
  - estados/transiciones validados por métodos de entidad
  - tests unitarios de invariantes críticos
- Application:
  - use cases sin imports de FastAPI/SQLAlchemy/Repository concreto
  - puertos explícitos para reminders y notifications
- Infrastructure:
  - implementación de puertos con errores DB homogéneos
  - mappers consistentes y timezone-safe
- Presentation:
  - endpoints consumen use cases (no repos directos)
  - validaciones y responses consistentes con contratos v1/v2
- DI:
  - providers de puertos + use cases desacoplados y testeables

## 5) Plan incremental sin romper API (para 7.2)

1. PR A: introducir puertos + use cases de notifications y adaptar DI.
2. PR B: migrar presentation a use cases manteniendo v1.
3. PR C: publicar v2 y dejar v1 en deprecación controlada.
4. PR D: cerrar cobertura y casos borde críticos (input de 7.3).
