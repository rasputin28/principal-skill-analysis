# Diseño experimental

## Estimando primario: valor de Shapley exacto

φᵢ = promedio, sobre todas las combinaciones de otras skills, de cuánto mejora el resultado
cuando se agrega la skill i. Elegido por la propiedad de eficiencia: Σφᵢ = v(S) − v(∅).
Esto hace del Pareto una descomposición real, no una suma arbitraria.

Implementado en `psa/estimate.py::shapley_exact_by_task` vía la transformada de Möbius
(dividendos). Eficiencia verificable con `efficiency_residual()` (debe ser ~0 a 1e-12).

## Etapas del diseño

| etapa | configuraciones | propósito |
|---|---|---|
| piloto | 2 (vacía + catálogo completo) | banda informativa: clasificar tareas por dificultad |
| cribado | 48 (PB Res-IV + foldover) | estimar φᵢ para todos y retener top-k |
| exacto | 2^k (e.g. 128 con k=7) | Shapley exacto, bootstrap sobre tareas |
| validación | presupuesto TBD | control de contaminación sobre tareas post-corte |

## Diseño factorial fraccionado

Plackett–Burman Res-IV + foldover. 48 configuraciones para N≤23 skills.

- **Res-IV**: efectos principales NO aliasados con interacciones de 2 factores. Res-III se
  rechazó explícitamente: habría aliasado exactamente las skills que solo funcionan acompañadas.
- **Foldover**: cada elección invertida en la segunda mitad. Elimina un tipo específico de
  aliasing y dobla las corridas.
- **Balance y ortogonalidad**: cada skill aparece en exactamente la mitad de las configuraciones;
  toda par de skills cubre los cuatro cuadrantes en igual proporción.

## Banda informativa

Filtro previo al cribado: se descartan tareas que la línea base resuelve siempre (>umbral alto)
o nunca (<umbral bajo). Solo las tareas intermedias revelan algo sobre las skills.
Los umbrales son [[pendiente-nombre]] hasta que Joel los decida (campo en
`preregistration/run-0-pilot.md`).

## Bootstrap

Sobre tareas, no sobre corridas. El pareo por tarea (misma tarea, misma semilla, mismo modelo,
solo cambia la configuración) es la palanca dominante de reducción de ruido. El bootstrap replica
ese pareo al remuestrear tareas con reemplazo. 2000 resamples, alpha = 0.05.

## Controles de calibración (ver [[controls]])

Criterio 1 (negativo): φ_placebo no excluye cero → instrumento calibrado.
Criterio 2 (positivo): φ_saboteador < 0 y excluye cero → el instrumento detecta daño deliberado.
Si el criterio 1 falla, no se reporta nada de esa corrida.
