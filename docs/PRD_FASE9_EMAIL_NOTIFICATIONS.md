# PRD — Fase 9: Email Notifications (Todo Reminders)

**Proyecto:** Monolith API
**Fase:** 9
**Prioridad:** 🟡 Por definir
**Estado:** ⏳ Pendiente
**Fecha:** 2026-05-01

---

## Contexto

El sistema ya tiene:
- TODOs con `due_date` (campo `datetime | None` en la entidad `Todo`)
- Entidad `Notification` con estados `PENDING → SENT → READ` y transiciones validadas
- `ProcessRemindersUseCase` que busca TODOs con due_date próximo y crea notificaciones en `PENDING`, pero **no envía emails**
- `ResendEmailSender` integrado y funcional (usado para OTP)
- `AuthDatasource` con `get_user_by_id` disponible
- Endpoint `/internal/reminders/process` (verificar si existe o crear)

**Gap a resolver:** el job de recordatorios no envía emails. Esta fase agrega el envío real via Resend y protege el endpoint interno.

---

## Objetivo

Cuando un usuario autenticado crea un TODO con `due_date`, al acercarse esa fecha recibe un email de recordatorio en la dirección asociada a su cuenta. El job es disparado por cron-job.org via un endpoint interno protegido por token.

---

## Flujo completo esperado

```
Usuario autenticado → crea TODO "Estudiar" con due_date = mañana
                              ↓
cron-job.org → POST /internal/v1/reminders/process (con header X-Internal-Token)
                              ↓
ProcessRemindersUseCase:
  1. Busca TODOs con due_date dentro de N días (default: 1)
  2. Para cada TODO:
     a. Obtener el email del owner via AuthDatasource.get_user_by_id(todo.user_id)
     b. Crear notificación en estado PENDING
     c. Enviar email via ResendEmailSender
     d. Si éxito → marcar notificación como SENT
     e. Si falla → dejar en PENDING (reintento en próximo cron), loguear error
  3. Retornar { processed, created, sent, failed }
                              ↓
Usuario recibe email + puede ver notificación en GET /v1/notifications
```

---

## Archivos a modificar

### 1. `app/core/config/env_config.py`

Agregar campo opcional:

```python
internal_api_key: str | None = None
```

---

### 2. `.env.example`

Agregar al final:

```env
# Internal API (para cron-job.org)
INTERNAL_API_KEY=
```

---

### 3. `app/features/auth/infrastructure/providers/resend_email_sender.py`

Agregar soporte para el nuevo purpose `todo_reminder`:

```python
PURPOSE_SUBJECTS = {
    "password_change": "Reset your password — MauriDev API",
    "todo_reminder": "Recordatorio de tarea — MauriDev API",  # NUEVO
}

PURPOSE_TEXT = {
    "password_change": "Use this code to reset your password.",
    "todo_reminder": None,  # NUEVO — usa template propio, no el de OTP
}
```

Agregar método `send_todo_reminder` (o extender `send_otp` — ver nota de diseño abajo).

**Nota de diseño:** Evaluar si es mejor:
- **Opción A (recomendada):** Agregar nuevo método `send_reminder(to_email, todo_title, due_date)` al contrato `EmailSender` con su propio template HTML
- **Opción B:** Reutilizar `send_otp` con un purpose nuevo (más simple pero semánticamente forzado)

Implementar **Opción A**. El template HTML debe ser consistente con el existente (mismo estilo que el de OTP).

---

### 4. `app/features/auth/application/contracts/email_sender.py`

Agregar método abstracto:

```python
@abstractmethod
def send_reminder(self, to_email: str, todo_title: str, due_date: str) -> None:
    """Send a todo reminder email to the user."""
    pass
```

---

### 5. `app/features/auth/infrastructure/providers/resend_email_sender.py`

Implementar `send_reminder` con template HTML propio:

```python
REMINDER_HTML_TEMPLATE = """
<div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
  <h2 style="color: #1a1a1a; margin-bottom: 8px;">Recordatorio de tarea</h2>
  <p style="color: #555; margin-bottom: 24px;">Tu tarea vence pronto:</p>
  <div style="background: #f4f4f4; border-radius: 8px; padding: 24px; text-align: center;">
    <span style="font-size: 20px; font-weight: bold; color: #1a1a1a;">{todo_title}</span>
    <p style="color: #888; margin-top: 8px;">Fecha límite: {due_date}</p>
  </div>
  <p style="color: #888; font-size: 13px; margin-top: 24px;">
    Ingresá a la app para marcarla como completada.
  </p>
</div>
"""

def send_reminder(self, to_email: str, todo_title: str, due_date: str) -> None:
    # Implementar llamada a Resend con el template REMINDER_HTML_TEMPLATE
    ...
```

---

### 6. `app/features/auth/infrastructure/providers/console_email_sender.py`

Agregar implementación de `send_reminder` para desarrollo local:

```python
def send_reminder(self, to_email: str, todo_title: str, due_date: str) -> None:
    print(f"[REMINDER] to={to_email} todo='{todo_title}' due={due_date}")
```

---

### 7. `app/features/notifications/application/usecases/process_reminders_use_case.py`

Reemplazar la implementación actual. El use case debe recibir tres dependencias:

```python
class ProcessRemindersUseCase:
    def __init__(
        self,
        todo_datasource: TodoDatasource,
        notification_datasource: NotificationDatasource,
        auth_datasource: AuthDatasource,   # NUEVA
        email_sender: EmailSender,          # NUEVA
    ):
```

Flujo del método `execute(days_ahead: int = 1) -> dict`:

```python
def execute(self, days_ahead: int = 1) -> dict:
    now = datetime.now(UTC)
    todos = self.todo_datasource.get_todos_with_upcoming_due_date(days_ahead, now)

    created = 0
    sent = 0
    failed = 0

    for todo in todos:
        try:
            # 1. Obtener usuario
            user = self.auth_datasource.get_user_by_id(todo.user_id)
            if user is None:
                logger.warning(f"User not found for todo {todo.id}, skipping")
                failed += 1
                continue

            # 2. Crear notificación en PENDING
            notification = Notification.create_for_todo_reminder(
                user_id=todo.user_id,
                todo_id=todo.id,
                todo_title=todo.title,
            )
            saved_notification = self.notification_datasource.create(notification)
            created += 1

            # 3. Enviar email
            due_date_str = todo.due_date.strftime("%d/%m/%Y %H:%M") if todo.due_date else ""
            self.email_sender.send_reminder(
                to_email=user.email.value,
                todo_title=todo.title,
                due_date=due_date_str,
            )

            # 4. Marcar como SENT
            self.notification_datasource.mark_as_sent(saved_notification.id)
            sent += 1

        except Exception as e:
            # Dejar en PENDING para reintento
            failed += 1
            logger.error(f"Failed to process reminder for todo {todo.id}: {e}")

    return {"processed": len(todos), "created": created, "sent": sent, "failed": failed}
```

---

### 8. `app/features/notifications/presentation/api.py`

Agregar endpoint interno protegido. Verificar si ya existe `/internal/reminders/process`. Si no existe, crearlo:

```python
@router.post("/internal/v1/reminders/process")
def process_reminders(
    request: Request,
    use_case: Annotated[ProcessRemindersUseCase, Depends(get_process_reminders_use_case)],
    env_config: Annotated[EnvConfig, Depends(get_env_config)],
) -> dict:
    """Internal endpoint for cron-job.org to trigger reminder processing."""
    token = request.headers.get("X-Internal-Token")
    if not env_config.internal_api_key or token != env_config.internal_api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = use_case.execute(days_ahead=1)
    return result
```

**Importante:** Este endpoint debe registrarse en `app/main.py` si está en un router separado. Verificar el montaje actual de `notifications_v1_router`.

---

### 9. `app/features/notifications/di/dependencies.py`

Agregar provider para `ProcessRemindersUseCase`:

```python
def get_process_reminders_use_case(
    todo_datasource: Annotated[TodoDatasource, Depends(get_todo_repository)],
    notification_datasource: Annotated[NotificationDatasource, Depends(get_notification_datasource)],
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> ProcessRemindersUseCase:
    return ProcessRemindersUseCase(
        todo_datasource=todo_datasource,
        notification_datasource=notification_datasource,
        auth_datasource=auth_datasource,
        email_sender=email_sender,
    )
```

Las dependencias `get_todo_repository`, `get_auth_repository` y `get_email_sender` ya existen en sus respectivos módulos de DI. Importarlas correctamente.

---

## Archivos a crear

### `tests/features/notifications/application/usecases/test_process_reminders_use_case.py`

Tests unitarios requeridos (todos con `Mock(spec=...)`):

```
test_should_send_email_and_mark_as_sent_when_todo_has_upcoming_due_date
  → todo con due_date próximo, user existe, email OK → notificación SENT, sent=1

test_should_leave_notification_pending_when_email_send_fails
  → email_sender.send_reminder lanza excepción → notificación queda en PENDING, failed=1

test_should_skip_todo_when_user_not_found
  → auth_datasource.get_user_by_id retorna None → failed=1, no crea notificación

test_should_return_correct_counts
  → 3 todos: 2 OK, 1 falla → { processed: 3, created: 2 o 3, sent: 2, failed: 1 }

test_should_return_empty_counts_when_no_todos_due
  → get_todos_with_upcoming_due_date retorna [] → { processed: 0, created: 0, sent: 0, failed: 0 }

test_should_process_multiple_todos_independently
  → cada todo se procesa de forma independiente, fallo en uno no afecta los demás
```

---

## Criterios de aceptación

- [ ] `ProcessRemindersUseCase` acepta `AuthDatasource` y `EmailSender` como dependencias
- [ ] El flujo crea notificación → envía email → marca SENT en caso exitoso
- [ ] En caso de fallo de email, la notificación queda en `PENDING` (reintentable)
- [ ] Si el usuario no existe, se loguea warning y se salta sin romper el job
- [ ] El endpoint `/internal/v1/reminders/process` retorna 401 sin `X-Internal-Token` válido
- [ ] El endpoint retorna 200 con `{ processed, created, sent, failed }` con token válido
- [ ] `ConsoleEmailSender` implementa `send_reminder` para desarrollo local
- [ ] `ResendEmailSender` implementa `send_reminder` con template HTML propio
- [ ] `INTERNAL_API_KEY` agregada a `env_config.py` y `.env.example`
- [ ] Tests unitarios de `ProcessRemindersUseCase` pasan con cobertura de casos feliz y triste
- [ ] Suite completa pasa sin regresiones

---

## Variables de entorno nuevas

| Variable | Descripción | Requerida |
|---|---|---|
| `INTERNAL_API_KEY` | Token secreto para proteger `/internal/v1/reminders/process` | Sí (en producción) |

---

## Configuración cron-job.org

Una vez deployado:

- **URL:** `https://api-monolith.onrender.com/internal/v1/reminders/process`
- **Método:** `POST`
- **Header:** `X-Internal-Token: <valor de INTERNAL_API_KEY>`
- **Frecuencia sugerida:** cada hora o cada 6 horas según necesidad

---

## Notas para el agente

1. **No romper contratos existentes.** `EmailSender` es un ABC — al agregar `send_reminder` como método abstracto, todas las implementaciones deben actualizarlo (`ResendEmailSender`, `ConsoleEmailSender`, `SmtpEmailSender` si aplica).
2. **El test E2E existente** usa `CaptureEmailSender` — agregar `send_reminder` como no-op en esa clase también.
3. **Verificar** si el endpoint interno ya existe en alguna forma antes de crearlo para evitar duplicados.
4. **Mantener** el patrón de tests existente: unit tests con `Mock(spec=...)`, nombres descriptivos en español tipo `test_should_...`.
5. **Convención de commits:** `feat: agrega envío de email en process reminders use case`
