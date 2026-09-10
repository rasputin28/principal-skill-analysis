# PSA — Principal Skill Analysis

Instrumento empírico para medir qué skills de un catálogo de agente (y qué combinaciones)
explican el rendimiento en un benchmark. El catálogo es un parámetro de entrada: se apunta a
cualquier repo de skills, se fija por commit, se mide.

**Estado (2026-09-10):** Pre-corrida. Runner real implementado. Pre-registro en borrador
(4 campos pendientes de decisión humana). Sin corridas reales ejecutadas aún.
Suite de tests: 96 passed (verificado 2026-09-10). Requiere `pip install -e .` en el venv
antes de la primera ejecución de tests en entorno limpio.

**Bloqueo persistente (4ª noche):** Las 3 tareas de ejecución (piloto de banda, controles,
corrida piloto) siguen sin poder correr. Dos causas independientes: (1) pre-registro tiene
4 campos `[PENDIENTE HUMANO]` sin llenar — ejecutar sin ellos destruye la integridad del
pre-registro; (2) entorno SWE-bench de evaluación no está configurado. Sin ambas resueltas,
el sistema NOCHE no puede avanzar aunque se autorice el gasto de API.

**Nombre:** PSA = Principal Skill Analysis. [[pendiente-nombre]] — Joel escribió "PCS" en un
mensaje; requiere confirmar PSA vs. PCS antes de cualquier referencia externa.

## Componentes principales

- [[runner]] — Protocolo de ejecución; `ClaudeCodeRunner` implementado 2026-09-07
- [[design]] — Diseño experimental: factorial fraccionado Res-IV, Shapley exacto
- [[catalogs]] — Los catálogos bajo prueba y la regla de selección
- [[preregistration]] — El proceso de pre-registro y su estado actual
- [[controls]] — Placebo y saboteador: calibración del instrumento

## Archivos clave

| archivo | propósito |
|---|---|
| `psa/runner/claude_code.py` | `ClaudeCodeRunner` — harness de producción |
| `psa/runner/base.py` | Protocolo `Runner`, `StubRunner`, `RunOutcome` |
| `psa/estimate.py` | Shapley exacto, bootstrap, ejes latentes |
| `psa/ledger.py` | JSONL de mediciones; frontera ejecución/análisis |
| `psa/report.py` | `guard()`, `report_card()`, `controls_verdict()` |
| `psa/controls.py` | Generadores de placebo y saboteador |
| `preregistration/run-0-pilot.md` | Pre-registro piloto (borrador, 4 campos abiertos) |
| `preregistration/catalog-selection.md` | Regla y resultado de selección de catálogos |

## Restricciones activas

- No correr simulaciones (instrucción de Joel 2026-09-06).
- No gastar API budget sin autorización escrita en `CLAUDE.md` del proyecto.
- `StubRunner` está bloqueado por `report.guard()` — sus outputs son hashes, no mediciones.
