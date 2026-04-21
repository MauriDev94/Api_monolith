# Contributing

## Flujo de trabajo Git

Todo cambio al proyecto, sin excepción, sigue este flujo.

### 1. Partir desde main actualizado

```bash
git checkout main
git pull origin main
```

Nunca trabajar directamente sobre main ni sobre una rama desactualizada.

---

### 2. Crear una rama descriptiva

```bash
git checkout -b feature/nombre-descriptivo
```

**Convención de nombres:**

| Prefijo | Cuándo usarlo |
|---|---|
| `feature/` | Feature nuevo |
| `fix/` | Bug fix |
| `refactor/` | Refactor sin cambio de comportamiento |
| `test/` | Agregar o corregir tests |
| `chore/` | Dependencias, configs, tareas de mantenimiento |
| `docs/` | Documentación |
| `release/` | Preparación de versión |

Ejemplos válidos:
```
feature/auth-jwt
fix/email-validation
refactor/user-entity
chore/update-dependencies
```

---

### 3. Hacer los cambios

Trabajar en la rama. Commitear en incrementos lógicos — no todo junto al final.

---

### 4. Commits con Conventional Commits

```bash
git add .
git commit -m "tipo: descripción corta en minúscula"
```

**Tipos válidos:**

| Tipo | Cuándo usarlo |
|---|---|
| `feat` | Feature nuevo |
| `fix` | Bug fix |
| `refactor` | Refactor sin cambio de comportamiento |
| `test` | Tests |
| `docs` | Documentación |
| `chore` | Tareas de mantenimiento |
| `perf` | Mejora de performance |

**Reglas del mensaje:**
- Verbo en presente: `agrega`, `corrige`, `extrae` — no `agregué` ni `agregando`
- Minúscula siempre
- Sin punto al final
- Máximo 72 caracteres

Ejemplos válidos:
```
feat: agrega endpoint de login con JWT
fix: corrige validación de emails con signo +
refactor: extrae lógica de hash a value object
test: agrega casos borde en Email VO
chore: actualiza dependencias a versiones estables
```

---

### 5. Subir la rama

```bash
git push origin feature/nombre-descriptivo
```

---

### 6. Abrir Pull Request en GitHub

En GitHub aparece el botón **"Compare & pull request"** automáticamente.

**El PR debe tener:**
- Título en Conventional Commits: `feat: agrega autenticación JWT`
- Descripción con qué cambiaste y por qué (no cómo)
- Referencia al issue si existe: `Closes #12`

**Template de descripción de PR (copiar y usar en cada PR):**

```markdown
## Summary
[Una línea: qué hace este PR]

## Type of Change
- [ ] Feature
- [ ] Fix
- [ ] Docs
- [ ] Chore

## Checklist
- [ ] Tests passing
- [ ] CI en verde (pre-commit)

## Cambios
### [Nombre del cambio]
- [ ] [Descripcion del cambio]

## How to Test
1. [Paso 1]
2. [Paso 2]

## Risks and Rollback
[Bajo/Medio/Alto riesgo] - [Descripción del rollback]
```

**Estrategia de merge:** usar siempre **Squash and merge** para mantener el historial de main limpio.

---

### 7. Después del merge

```bash
git checkout main
git pull origin main
git branch -d feature/nombre-descriptivo
```

GitHub ofrece borrar la rama remota automáticamente con el botón **"Delete branch"** después del merge. Usarlo siempre.

---

## Reglas generales

- Nunca commitear directamente a `main`
- Nunca hacer force push a `main`
- Una rama = un propósito
- Si el PR crece demasiado, dividirlo en PRs más pequeños
- Los tests deben pasar antes de pedir review
