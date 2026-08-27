## 📌 Issue relacionado

Closes #<!-- número del issue -->

## 🧠 Resumen

_Qué hace este PR, en 2-3 líneas._

## 📂 Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `path/to/file` | _Qué cambió y por qué_ |

## ✅ Checklist

- [ ] Lint + format pasan: `ruff check . && ruff format --check .`
- [ ] Type checking pasa: `mypy app`
- [ ] Tests pasan: `pytest -q` → N passed, 0 failed
- [ ] Sin lógica de negocio en endpoints (presentación delgada)
- [ ] Sin imports de SQLAlchemy en `application/` ni `presentation/` (DIP)
- [ ] Conventional commits
- [ ] Sin migraciones huérfanas: `alembic check`

## 🧪 Cómo probar

```bash
ruff check . && ruff format --check . && mypy app
pytest -q
```

## 📝 Notas técnicas

<!-- Opcional — gotchas, decisiones de diseño no obvias, bugs encontrados -->
