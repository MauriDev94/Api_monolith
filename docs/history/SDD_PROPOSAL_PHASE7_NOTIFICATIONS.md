# Proposal: Refactor Notifications (Fase 7)

## Intent

Corregir acoplamientos de capas en notifications (presentation/application/infra), mejorar mantenibilidad y agregar versionado de API para evolucionar contratos sin romper consumidores.

## Scope

### In Scope
- Refactor de notifications por capas con contratos explícitos y casos de uso consistentes.
- Ajuste de API con estrategia versión B (compatibilidad + endpoints versionados).
- Endurecimiento de observabilidad, errores homogéneos y cobertura de casos borde críticos.

### Out of Scope
- Implementar nuevos canales (email/push/webhook).
- Cambios en auth/SSO/OTP fuera de integración mínima requerida.

## Capabilities

### New Capabilities
- `notifications-api-v2`: contratos versionados para listar y marcar leídas con respuestas consistentes.
- `notifications-reminders-orchestration`: orquestación de recordatorios desacoplada de ORM en application.
- `notifications-observability`: trazabilidad y logs estructurados en flujos críticos.

### Modified Capabilities
- None (no existen specs previas en `openspec/specs` para delta formal).

## Approach

Aplicar refactor incremental en tres pasos: (1) diagnóstico por capa y matriz de contratos no rompibles, (2) migración interna a use cases + puertos + DI limpio, (3) publicación de API versionada con compatibilidad temporal y deprecación explícita.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/features/notifications/domain/**` | Modified | Invariantes y estados de notificación más estrictos |
| `app/features/notifications/application/**` | Modified | Use cases explícitos y puertos de recordatorios |
| `app/features/notifications/infrastructure/**` | Modified | Repositorios/mappers robustos y errores homogéneos |
| `app/features/notifications/presentation/**` | Modified | Contratos API v1/v2 y validaciones |
| `app/features/notifications/di/dependencies.py` | Modified | Providers desacoplados y testeables |
| `tests/features/notifications/**` | New/Modified | Suite por capa + casos borde |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Incompatibilidad de clientes API actuales | Med | Mantener v1 temporal + deprecación documentada |
| Regresiones en reminders | Med | Tests de integración + E2E focalizados |
| Drift de arquitectura entre features | Low | Reusar patrón users como baseline |

## Rollback Plan

Revertir PRs de Fase 7 en orden inverso (7.3 → 7.2 → 7.1), mantener endpoints v1 activos y restaurar wiring previo en DI si aparece regresión severa.

## Dependencies

- `roadmap.md` actualizado y aprobado como fuente de verdad de Fase 7.
- Pipeline CI (quality/tests) en verde antes de merge por punto.

## Success Criteria

- [ ] Notifications alineado con patrón clean architecture usado en users.
- [ ] API versionada publicada con compatibilidad controlada y deprecaciones claras.
- [ ] Cobertura de notifications >= 90% en casos críticos + borde.
- [ ] Logs/errores trazables con `request_id` en flujos de notifications.
