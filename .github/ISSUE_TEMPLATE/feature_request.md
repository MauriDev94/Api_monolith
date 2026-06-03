---
name: "✨ Feature request"
about: Proponer una nueva funcionalidad o mejora
title: "feat: <descripción breve>"
labels: ["enhancement"]
assignees: ""
---

## Problema / necesidad
<!-- ¿Qué problema resuelve? ¿Por qué vale la pena? No describas la solución todavía. -->

## Propuesta
<!-- ¿Cómo lo resolverías? Endpoints, flujo, comportamiento esperado. -->

## Capas involucradas
- [ ] Domain (nuevas entidades / value objects / reglas)
- [ ] Application (nuevos use cases / contratos)
- [ ] Infrastructure (repositorios / providers / migraciones)
- [ ] Presentation (routers / schemas / mappers)

## Diseño de API (si aplica)
- **Endpoint:** `<METHOD> /ruta`
- **Request:**
- **Response:**

## Alternativas consideradas
<!-- ¿Qué otras opciones evaluaste y por qué las descartaste? -->

## Criterios de aceptación
- [ ] TDD: tests primero
- [ ] Regla de dependencia respetada (la capa interna no conoce a la externa)
- [ ] DIP: sin imports de SQLAlchemy en `application/` ni `presentation/`
- [ ] Migración Alembic incluida si toca el esquema
- [ ] `ruff check .` + `black --check .` + `mypy app` en verde
- [ ] `pytest -q` en verde, coverage sin bajar del gate
