# AVANCES — PSA — noche 2026-09-08

## Hecho

### Verificación de suite de tests
- **Comando:** `.venv/bin/pip install -e . && .venv/bin/pytest --tb=no -q`
- **Resultado:** 96 passed, 0 failed (idéntico a 2026-09-07)
- **Hallazgo:** el paquete `psa` requiere `pip install -e .` para que pytest lo encuentre.
  Sin ese paso, los 4 módulos de test fallan con `ModuleNotFoundError: No module named 'psa'`.
  La suite no está rota — es un problema de entorno de ejecución, no de código.

### Wiki actualizada
- `wiki/INDEX.md`: fecha actualizada a 2026-09-08, nota de instalación añadida.

---

## Atascado / Fallas

### Noche sin producción nueva

Las 3 tareas de código siguen bloqueadas por las mismas razones que la noche anterior:

| tarea | bloqueante |
|---|---|
| Piloto de banda informativa | Sin autorización de gasto de API en `CLAUDE.md` |
| Corrida de controles | Sin autorización de gasto de API en `CLAUDE.md` |
| Corrida piloto completa | Bloqueada por las dos anteriores + misma restricción |

No hubo contexto nuevo en inbox (vacío). No hubo notas ni grabaciones del día con accionables
para PSA. La constitución del sistema NOCHE prohíbe gastar dinero sin autorización escrita;
esa autorización no está en el `CLAUDE.md` del proyecto. El bloqueo es correcto.

---

## Decisiones pendientes (para Joel)

Siguen abiertas las 6 de la noche anterior:

1. **Autorizar gasto de API budget** — añadir a `CLAUDE.md` del proyecto:
   > `Autorizado: ClaudeCodeRunner puede gastar hasta [N] dólares en corridas PSA por noche.`

2. **Banda informativa** — umbrales inferior y superior de resolve-rate de la línea base
   (sugerido: 0.10–0.90). Llenar en `preregistration/run-0-pilot.md` y recommitear.

3. **Modelo** — identificador exacto (e.g. `claude-sonnet-5-20251001`).

4. **Semillas** — lista fija (e.g. `[0, 1, 2]`).

5. **k y repeticiones por celda** — k determina 2^k configuraciones en la etapa exacta.

6. **Nombre PSA vs. PCS** — confirmar antes de cualquier referencia externa.

---

## Entregables

| artefacto | ruta | estado |
|---|---|---|
| Runner real | `psa/runner/claude_code.py` | listo, 18 tests verdes |
| Tests del runner | `tests/test_runner.py` | 18 passed |
| Suite completa | `tests/` | 96 passed (verificado 2026-09-08) |
| Pre-registro piloto | `preregistration/run-0-pilot.md` | borrador — 4 campos abiertos |
| Wiki PSA | `wiki/` (6 páginas) | al día |
| Branch runner | `noche/2026-09-07-runner` | commiteado |
| Branch preregistration + wiki | `noche/2026-09-07-preregistration` | commiteado |
