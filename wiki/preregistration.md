# Pre-registro

El instrumento del registered report. Se commiten ANTES de cualquier corrida los campos que,
de quedar abiertos, serían grados de libertad del investigador.

## Archivo de instancia activa

`preregistration/run-0-pilot.md` — borrador desde 2026-09-07.

**Estado:** 4 campos abiertos que requieren decisión de Joel antes de la primera corrida:
1. **Banda informativa** — umbrales inferior y superior de resolve-rate de la línea base.
2. **Modelo** — identificador exacto (e.g. `claude-sonnet-5-20251001`).
3. **Semillas** — lista fija (e.g. `[0, 1, 2]`).
4. **k y repeticiones** — supervivientes del cribado y reps por celda (determinan el presupuesto).

El campo de `k` es el más delicado: determina el tamaño del diseño exacto (2^k configuraciones)
y por lo tanto el costo total. No puede elegirse después de ver los resultados del cribado.

## Reglas del pre-registro

- Cada corrida real tiene su propio archivo de pre-registro, commiteado antes de correr.
- Cualquier desviación del documento se registra en `preregistration/<run>-deviations.md` con
  su razón y fecha, y se reporta junto con los resultados.
- El pre-registro no es una promesa de que los resultados sean positivos — es un compromiso de que
  el análisis fue decidido antes de ver los datos.

## Plantilla

`preregistration/TEMPLATE.md` — el formulario en blanco. No editarlo directamente; copiar
a un nuevo archivo por corrida.

## Selección de catálogos

Documentada en `preregistration/catalog-selection.md` (2026-09-06). Ver [[catalogs]].
