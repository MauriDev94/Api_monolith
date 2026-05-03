# PR Conventions

**Versión:** 2.0 (2026-05-02)

---

## Reglas para generar PR bodies

### Regla principal
**Eliminar líneas vacías, no marcarlas.** Solo incluir checkbox que aplican al cambio.

### Type of Change
- Solo marcar el tipo que corresponde
- Eliminar las demás opciones vacías

Ejemplo: solo feat → subir solo `- [x] feat — feature nuevo`

### Changes por capa
- Solo incluir las capas que tienen cambios
- Eliminar las capas vacías

Ejemplo: solo Infrastructure → subir solo `### Infrastructure` con sus cambios

### Checklist
- Mantener solo los relevantes para el cambio
- Eliminar los no aplicables

---

## Proceso de creación de PR

1. `git diff --name-only` para ver archivos modificados
2. Leer convenciones
3. Determinar Type of Change según archivos
4. Determinar qué capas aplican según archivos
5. Generar body filtrado (solo checkbox marcados)
6. Crear PR con gh pr create
