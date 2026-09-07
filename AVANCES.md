# AVANCES — PSA — noche 2026-09-07

## Hecho

### [codigo] ClaudeCodeRunner implementado
- **Branch:** `noche/2026-09-07-runner` (commit c736956)
- **Archivo:** `psa/runner/claude_code.py`
- **Tests:** 18 nuevos en `tests/test_runner.py` — todos verdes. Suite completa: 96 passed (0 failed).
- Runner llama al CLI `claude` vía subprocess, pasa `CLAUDE_SKILLS_DIR=workspace`, parsea
  `--output-format json` del transcript para extraer llamadas reales a `Skill` tool.
- `HarnessUnsupported` se lanza (en lugar de datos silenciosamente incorrectos) cuando el
  transcript no tiene clave `"messages"`, el binary no existe, timeout, o exit code ≠ 0.
- `ClaudeCodeRunner` satisface el protocolo `Runner` (verificado en test).
- `report.guard()` sigue bloqueando `StubRunner` — no se rompió el contrato existente.

### [doc] Pre-registro piloto en borrador
- **Branch:** `noche/2026-09-07-preregistration` (commit 5b66b49)
- **Archivo:** `preregistration/run-0-pilot.md`
- Llena todo lo derivable de la sesión 2026-09-06: catálogos, benchmark (SWE-bench Verified),
  harness, desenlace primario (Shapley φᵢ), etapas del diseño, hipótesis H1–H5 con umbrales
  numéricos, reglas de parada y reporte.
- **No puede commitarse como pre-registro final** hasta que 4 campos queden fijos (ver sección
  Decisiones pendientes).

### Wiki inicializada
- **Branch:** `noche/2026-09-07-preregistration` (commit eeae73e)
- 6 páginas: INDEX, runner, design, catalogs, controls, preregistration, pendiente-nombre.

---

## Atascado / Fallas

### [codigo] Piloto de banda informativa — NO ejecutado
- **Razón:** requiere corridas reales con la API de Claude (gasto de dinero). El CLAUDE.md del
  proyecto no autoriza gasto de API budget por escrito. Constitución del sistema NOCHE: "gastar
  dinero o contratar servicios" requiere autorización explícita.
- **No es un error técnico** — el bloqueo es intencional y correcto.

### [codigo] Corrida de controles — NO ejecutada
- **Razón:** misma que arriba. Los controles requieren corridas reales.

### [codigo] Corrida piloto completa — NO ejecutada
- **Razón:** bloqueada por las dos anteriores, además de la misma restricción de presupuesto.

---

## Decisiones pendientes (para Joel)

1. **Autorizar gasto de API budget** para las corridas reales (piloto, controles, cribado).
   Sin esta autorización escrita en `CLAUDE.md`, el sistema NOCHE no puede ejecutar las
   tareas 3–5 de PENDIENTES.md. Añadir una línea como:
   > `Autorizado: ClaudeCodeRunner puede gastar hasta [N] dólares en corridas PSA por noche.`

2. **Banda informativa** — decidir umbrales inferior y superior de resolve-rate de la línea
   base (e.g. 0.10–0.90). Llenar el campo en `preregistration/run-0-pilot.md` y recommitear.

3. **Modelo** — especificar el identificador exacto del modelo (e.g. `claude-sonnet-5-20251001`).

4. **Semillas** — lista fija de seeds (e.g. `[0, 1, 2]`). Fijar antes de la primera corrida.

5. **k y repeticiones por celda** — k determina 2^k configuraciones en la etapa exacta;
   repeticiones determina el presupuesto total. Ambos en `preregistration/run-0-pilot.md`.

6. **Nombre PSA vs. PCS** — confirmar antes de cualquier referencia externa.
   Ver `wiki/pendiente-nombre.md`.

---

## Entregables

| artefacto | ruta | estado |
|---|---|---|
| Runner real | `psa/runner/claude_code.py` | listo, 18 tests verdes |
| Tests del runner | `tests/test_runner.py` | 18 passed |
| Pre-registro piloto | `preregistration/run-0-pilot.md` | borrador — 4 campos abiertos |
| Wiki PSA | `wiki/` (6 páginas) | inicializada |
| Branch runner | `noche/2026-09-07-runner` | commiteado |
| Branch preregistration + wiki | `noche/2026-09-07-preregistration` | commiteado |
