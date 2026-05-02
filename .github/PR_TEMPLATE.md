# PR Creation — plantilla Unificada para Pull Requests

**Versión:** 2.2 (actualizada 2026-05-02)
**Proyecto:** Monolith

---

## Plantilla de PR

```markdown
## Summary
[Una línea: qué hace este PR y por qué]

## Type of Change
- [ ] Feature
- [ ] Fix
- [ ] Refactor
- [ ] Test
- [ ] Docs
- [ ] Chore

## Motivation
[Contexto breve: por qué fue necesario este cambio]

## Changes
### [Nombre del cambio]
- [ ] [Descripción del cambio] #número_ticket

## Checklist
- [ ] No hay secrets ni debug code

## How to Test
1. [Paso 1]
2. [Paso 2]

## Risks & Rollback
**Risk:** Bajo / Medio / Alto
**Rollback:** `git revert <commit>` / [instrucción específica]
```

---

## Uso

Copiar y usar en cada PR nuevo.
Marcar TODOS los tipos de cambio que aplican con `[x]`, incluso si uno es el principal.

---
