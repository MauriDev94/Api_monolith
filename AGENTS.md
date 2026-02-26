# AGENTS.md
# Guía de Arquitectura y Estándares del Proyecto

Este proyecto sigue estrictamente principios de Clean Code,
Clean Architecture y Domain-Driven Design (DDD).

---

## 🧱 Arquitectura (Clean Architecture)

Capas permitidas:

- domain/
  - Entidades
  - Value Objects
  - Reglas de negocio puras
  - NO depende de frameworks

- application/
  - Casos de uso
  - Orquestación de reglas de negocio
  - Interfaces (ports)

- infrastructure/
  - Implementaciones concretas
  - ORM, APIs externas, filesystem
  - Frameworks (FastAPI, SQLAlchemy, etc.)

- api/
  - Controllers / Routers
  - Adaptadores de entrada/salida

### Reglas
- El dominio NO puede importar nada externo
- La infraestructura depende de application y domain
- Nunca al revés

---

## 🧠 DDD

- Las entidades viven en `domain/entities`
- La lógica de negocio vive en el dominio
- Los repositorios son interfaces en application
- Las implementaciones concretas viven en infrastructure

---

## ✍️ Clean Code

- Nombres explícitos y descriptivos
- Funciones pequeñas (≤ 20 líneas)
- Una función = una responsabilidad
- No comentarios redundantes
- Preferir código autoexplicativo

---

## 🧪 Testing

- La lógica de dominio debe tener tests unitarios
- No testear frameworks
- Usar mocks para infraestructura

---

## 🚫 Prohibiciones

- No lógica de negocio en controllers
- No dependencias de SQLAlchemy/FastAPI en domain
- No clases "God object"
- No DTOs anémicos sin validación