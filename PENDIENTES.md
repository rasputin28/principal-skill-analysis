# PENDIENTES — PSA (Principal Skill Analysis)

## [2026-09-10] Triage

> Fuentes: inbox vacío. Sin contexto activo nuevo.
>
> Diagnóstico corregido esta noche: el bloqueo tiene DOS causas independientes, no una.
> (1) El pre-registro tiene 4 campos `[PENDIENTE HUMANO]` sin llenar — ejecutar sin ellos
> viola la integridad del estudio. (2) El entorno SWE-bench no está configurado en este equipo.
> Incluso con autorización de API budget, los runs no son posibles sin resolver ambos.
>
> Las 6 decisiones de Joel siguen sin resolverse (4ª noche consecutiva).
> Sin tareas nuevas — las tareas de ejecución existentes siguen pendientes.

_(sin tareas nuevas)_

---

## [2026-09-09] Triage

> Fuentes: inbox vacío. omna-brain MCP en timeout. MCP grabaciones no disponible. Sin contexto activo nuevo.
>
> Las 3 tareas de ejecución siguen bloqueadas por las 6 decisiones pendientes de Joel (API budget en CLAUDE.md, PSA vs PCS, modelo/semillas/k/repeticiones). Sin autorización escrita, el sistema NOCHE no puede ejecutar corridas. Sin tareas nuevas esta noche.

_(sin tareas nuevas)_

---

## [2026-09-08] Triage

> Fuentes: omna-brain activo hoy — ninguna nota del día genera accionables para PSA. Inbox vacío. Sin tareas nuevas.
>
> Estado: las 3 tareas de código (piloto de banda, controles, corrida piloto) siguen bloqueadas por 6 decisiones pendientes de Joel (ver AVANCES.md §Decisiones pendientes). Sin autorización de gasto de API escrita en `CLAUDE.md`, el sistema NOCHE no puede ejecutar corridas reales.
>
> URGENTE antes de próxima noche: (1) autorizar gasto de API budget añadiendo línea en `CLAUDE.md`, (2) confirmar nombre PSA vs. PCS, (3) fijar modelo, semillas, k y repeticiones por celda en pre-registro.

_(sin tareas nuevas — las tareas de ejecución existentes siguen pendientes de decisión humana)_

---

## [2026-09-07] Triage

> Fuentes: `inbox/sesion-2026-09-06-psa.md` (sesión de diseño 2026-09-06). Estado del repo: commit inicial `034f9f5` + docs, 40 tests pasando. `StubRunner` en su lugar; ninguna corrida real es posible hasta completar la tarea 1.

> Restricción activa: no correr simulaciones (instrucción explícita de Joel). El nulo es publicable — si ningún φ se distingue de cero, se reporta tal cual sin modificar el diseño.

> Decisión pendiente humana: confirmar nombre PSA vs. PCS antes de cualquier referencia externa.

- [x] [codigo] Implementar `Runner` real — `ClaudeCodeRunner` en `psa/runner/claude_code.py`. 18 tests verdes (branch noche/2026-09-07-runner, commit c736956). Hecho 2026-09-07.

- [x] [doc] Borrador de pre-registro en `preregistration/run-0-pilot.md`. 4 campos abiertos requieren decisión humana antes de poder recommitear como pre-registro final (ver AVANCES.md §Decisiones pendientes). Branch noche/2026-09-07-preregistration, commit 5b66b49. Hecho 2026-09-07.

- [ ] [codigo] Piloto de banda informativa sobre pocas tareas: correr la línea base (sin skills), clasificar tareas por dificultad y descartar extremos (siempre resueltas / nunca resueltas bajo la línea base). Origen: sesión 2026-09-06. Entregable: distribución de dificultad en `results/pilot-band.md`.

- [ ] [codigo] Correr controles ANTES de cualquier corrida de interés: placebo pareado en longitud y saboteador (`psa/controls.py`). Criterio de paso: φ del placebo NO excluye cero. Si falla, el instrumento está descalibrado — detener y reportar ese hecho como entregable. Origen: sesión 2026-09-06. Entregable: output de controles en `results/controls.md`.

- [ ] [codigo] Corrida piloto completa con Runner real, controles pasados y configuraciones del diseño fraccionado. Entregable: `results/report.md`. Si los controles fallan en el paso anterior, este paso no se ejecuta — el entregable es la evidencia del fallo. Origen: sesión 2026-09-06.
