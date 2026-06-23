"""Verifica que los modelos SQLAlchemy y las migraciones Alembic no tengan drift.

Equivale a `alembic check`: si un modelo declara algo que ninguna migración crea
(o al revés), este test falla. Es exactamente la red que habría cazado O1
(`todos.due_date` sin migración) antes de llegar a producción.
"""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine

# Drift pre-existente (acumulado porque `alembic check` nunca funcionó: env.py no
# importaba los modelos, ya corregido). Pendiente de reconciliar en la Fase 4:
#   - tabla `notifications` sin migración (la feature se elimina en Fase 4)
#   - FKs de `auth_otps`/`auth_refresh_tokens` declaradas en migración pero no en el modelo
#   - `users.google_id`: constraint único en la migración vs índice único en el modelo
# Al cerrar esos puntos, este xfail (strict) fallará y debe quitarse → gate duro permanente.
_PENDING_DRIFT_REASON = (
    "Reconciliación de esquema pendiente (notifications + FKs otp/refresh + google_id) — Fase 4"
)


# Tipo de test: Integration
@pytest.mark.xfail(reason=_PENDING_DRIFT_REASON, strict=True)
def test_models_match_migrations_no_drift(_postgres_engine: Engine) -> None:
    """No debe haber diferencias entre los modelos y el esquema migrado a head.

    `_postgres_engine` ya aplicó `alembic upgrade head` y dejó DATABASE_URL apuntando
    al contenedor; `command.check` compara los modelos contra ese esquema real.
    """
    command.check(Config("alembic.ini"))
