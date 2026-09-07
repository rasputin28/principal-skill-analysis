# Controles de calibración

Dos skills que no pertenecen a ningún catálogo bajo prueba y se inyectan en cada diseño.
Implementadas en `psa/controls.py`.

## Placebo (psa-placebo) — control negativo

Skill de igual longitud que la mediana del catálogo de unión pero con contenido inerte:
describe el layout de un repositorio en términos genéricos sin dar instrucciones ni pedir acción.

**Criterio 1:** φ_placebo debe NO excluir cero. Si excluye cero, el instrumento está midiendo
el efecto de la longitud del prompt, no el efecto de las skills. En ese caso no se reporta nada.

## Saboteador (psa-saboteur) — control positivo

Skill que da instrucciones deliberadamente malas: no corras los tests, no verifiques que el
cambio funciona, elige el primer edit plausible sin leer el código circundante.

**Criterio 2:** φ_saboteador debe ser negativo y excluir cero. Si el instrumento no puede
detectar daño deliberado de esta magnitud, no tiene sensibilidad suficiente para detectar mejoras
reales.

## Cuándo se corren

ANTES de cualquier corrida de interés. Si el criterio 1 falla, la corrida se detiene y se reporta
el fallo como el entregable — no se modifica el diseño para rescatarlo.

Ver `psa/report.py::controls_verdict()` para la implementación del veredicto.
Ver [[design]] para el contexto del diseño general.
