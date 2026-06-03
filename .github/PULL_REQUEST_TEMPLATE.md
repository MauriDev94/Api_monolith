## Summary
<!-- Una línea: qué hace este PR y por qué -->

## Why
<!-- Por qué es necesario este cambio? Qué problema resuelve o qué mejora aporta?
     Ej: "El endpoint /v1/users exponía datos de todos los usuarios sin restricción de rol" -->

## Type of Change
- [ ] `feat` — feature nuevo
- [ ] `fix` — bug fix
- [ ] `refactor` — refactor sin cambio de comportamiento
- [ ] `test` — tests
- [ ] `chore` — dependencias, configs, mantenimiento
- [ ] `docs` — documentación

## Changes
<!-- Lista de cambios concretos por capa -->
### Domain
- [ ]

### Application
- [ ]

### Infrastructure
- [ ]

### Presentation
- [ ]

## How to Test
1.
2.

## Checklist
- [ ] Tests pasan: `pytest -q`
- [ ] Lint + format en verde: `ruff check . && black --check .`
- [ ] Type checking en verde: `mypy app`
- [ ] Sin migraciones huérfanas: `alembic check`
- [ ] Coverage respeta el gate de CI (`--cov-fail-under`)
- [ ] **DIP:** sin imports de SQLAlchemy en `application/` ni `presentation/`
- [ ] **Presentación delgada:** sin lógica de negocio en los endpoints
- [ ] Sin imports no usados
- [ ] Docstrings en clases y métodos públicos nuevos

## Risks and Rollback
**Riesgo:** Bajo / Medio / Alto
**Rollback:**

## Related Issues
<!-- Closes #XX -->
