# Catálogos bajo prueba

Seleccionados 2026-09-06 según regla documentada en `preregistration/catalog-selection.md`.

## Seleccionados

| catálogo | autor | skills | licencia | última actualización |
|---|---|---|---|---|
| `obra/superpowers` | Jesse Vincent | 14 | MIT | 2026-09-04 |
| `addyosmani/agent-skills` | Addy Osmani | 25 | MIT | 2026-09-06 |

**Catálogo de unión:** 39 skills antes de deduplicación. Identificadores prefijados por catálogo
para que las colisiones (dos autores con skill para el mismo propósito) sean un hallazgo, no un
error.

## Regla de selección (resumen)

Elegible si: repo público con `SKILL.md` discernibles, licencia que permite redistribución,
actualizado en el último mes, número de skills dentro del rango del diseño sin requerir un
subconjunto elegido por el investigador. Se seleccionan los dos con más GitHub stars entre
los elegibles.

## Conflicto de interés declarado

`obra/superpowers` es el catálogo que el autor de este estudio usa en su trabajo diario. Se
incluye porque excluir el catálogo más popular sería una distorsión mayor. El incumbente debe
ser el caso más difícil de confirmar, no el más fácil.

## Descartados con razón

- `affaan-m/ECC` (898 skills): criterio (d) — requeriría subconjunto elegido por el investigador.
- `NousResearch/hermes-agent` (198 skills): criterio (d).
- `anthropics/skills`: criterio (b) — sin licencia permisiva; criterio extra: first-party.

## Cómo se fijan por commit

`psa/catalog.py::discover()` llama `git rev-parse HEAD` en la raíz del catálogo y registra el
commit en el `Catalog.commit`. El ledger almacena `catalog_commit` en cada `RunRecord`. Sin esto
la medición no es reproducible.
