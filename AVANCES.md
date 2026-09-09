# AVANCES — PSA — noche 2026-09-09

## Hecho

### Verificación de suite de tests
- **Comando:** `.venv/bin/pip install -e . && .venv/bin/pytest --tb=no -q`
- **Resultado:** 96 passed, 0 failed (idéntico a 2026-09-07 y 2026-09-08)
- La suite está intacta. Sin cambios de código esta noche.

### Wiki actualizada
- `wiki/INDEX.md`: fecha actualizada a 2026-09-09, nota de bloqueo persistente (3ª noche) añadida.

---

## Atascado / Fallas

### Noche sin producción nueva (3ª consecutiva)

Las 3 tareas de código siguen bloqueadas exactamente igual que las dos noches anteriores:

| tarea | bloqueante |
|---|---|
| Piloto de banda informativa | Sin autorización de gasto de API en `CLAUDE.md` |
| Corrida de controles | Sin autorización de gasto de API en `CLAUDE.md` |
| Corrida piloto completa | Bloqueada por las dos anteriores + misma restricción |

Inbox vacío. Sin notas, grabaciones ni contexto activo nuevo del día para PSA.
El bloqueo es correcto per constitución del sistema NOCHE.

---

## Decisiones pendientes (para Joel) — urgente

Llevan 3 noches sin resolverse. El sistema NOCHE no puede avanzar sin ellas.

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
| Suite completa | `tests/` | 96 passed (verificado 2026-09-09) |
| Pre-registro piloto | `preregistration/run-0-pilot.md` | borrador — 4 campos abiertos |
| Wiki PSA | `wiki/INDEX.md` | actualizada 2026-09-09 |
