---
name: "🐛 Bug report"
about: Reportar un comportamiento incorrecto en la API
title: "bug: <descripción breve>"
labels: ["bug"]
assignees: ""
---

## Descripción
<!-- ¿Qué está fallando? Sé concreto. -->

## Pasos para reproducir
1.
2.
3.

## Comportamiento esperado
<!-- ¿Qué debería pasar? -->

## Comportamiento actual
<!-- ¿Qué pasa en realidad? Incluí el status code y el body de la respuesta si aplica. -->

## Capa afectada
- [ ] Domain (entidades / value objects / reglas de negocio)
- [ ] Application (use cases / contratos)
- [ ] Infrastructure (repositorios / providers)
- [ ] Presentation (routers / schemas / mappers)
- [ ] Core / Config (middleware / exceptions / DB)

## Contexto técnico
- **Endpoint:** `<METHOD> /ruta`
- **`X-Request-ID`:** <!-- del header de la respuesta, para rastrear en logs -->
- **Entorno:** local / production

## Logs relevantes
```
<!-- pegá acá las líneas de log con el X-Request-ID -->
```

## Criterios de aceptación
- [ ] Test que reproduce el bug (falla antes del fix — TDD)
- [ ] Fix aplicado en la capa correcta
- [ ] `ruff check .` + `black --check .` + `mypy app` en verde
- [ ] `pytest -q` en verde
