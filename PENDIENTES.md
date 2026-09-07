# PENDIENTES — PSA (Principal Skill Analysis)

## [2026-09-07] Triage

> Fuentes: `inbox/sesion-2026-09-06-psa.md` (sesión de diseño 2026-09-06). Estado del repo: commit inicial `034f9f5` + docs, 40 tests pasando. `StubRunner` en su lugar; ninguna corrida real es posible hasta completar la tarea 1.

> Restricción activa: no correr simulaciones (instrucción explícita de Joel). El nulo es publicable — si ningún φ se distingue de cero, se reporta tal cual sin modificar el diseño.

> Decisión pendiente humana: confirmar nombre PSA vs. PCS antes de cualquier referencia externa.

- [x] [codigo] Implementar `Runner` real — `ClaudeCodeRunner` en `psa/runner/claude_code.py`. 18 tests verdes (branch noche/2026-09-07-runner, commit c736956). Hecho 2026-09-07.

- [x] [doc] Borrador de pre-registro en `preregistration/run-0-pilot.md`. 4 campos abiertos requieren decisión humana antes de poder recommitear como pre-registro final (ver AVANCES.md §Decisiones pendientes). Branch noche/2026-09-07-preregistration, commit 5b66b49. Hecho 2026-09-07.

- [ ] [codigo] Piloto de banda informativa sobre pocas tareas: correr la línea base (sin skills), clasificar tareas por dificultad y descartar extremos (siempre resueltas / nunca resueltas bajo la línea base). Origen: sesión 2026-09-06. Entregable: distribución de dificultad en `results/pilot-band.md`.

- [ ] [codigo] Correr controles ANTES de cualquier corrida de interés: placebo pareado en longitud y saboteador (`psa/controls.py`). Criterio de paso: φ del placebo NO excluye cero. Si falla, el instrumento está descalibrado — detener y reportar ese hecho como entregable. Origen: sesión 2026-09-06. Entregable: output de controles en `results/controls.md`.

- [ ] [codigo] Corrida piloto completa con Runner real, controles pasados y configuraciones del diseño fraccionado. Entregable: `results/report.md`. Si los controles fallan en el paso anterior, este paso no se ejecuta — el entregable es la evidencia del fallo. Origen: sesión 2026-09-06.
