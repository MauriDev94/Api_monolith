---
name: "📋 Tarea"
about: Paso de desarrollo, refactor o trabajo técnico
title: "task: <descripción breve>"
labels: ["task"]
assignees: ""
---

## Descripción
<!-- ¿Qué hay que hacer? Contexto técnico: capas, endpoints, contratos, etc. -->

## Alcance
<!-- Qué entra y qué NO entra en esta tarea. -->

## Criterios de aceptación
- [ ] TDD: tests primero
- [ ] Cambio aislado en la(s) capa(s) correcta(s)
- [ ] `ruff check .` + `ruff format --check .` + `mypy app` en verde
- [ ] `pytest -q` en verde
- [ ] Sin migraciones huérfanas: `alembic check`
- [ ] Commit con conventional commits
