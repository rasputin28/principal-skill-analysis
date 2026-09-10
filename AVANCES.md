# AVANCES — PSA — noche 2026-09-10

## Hecho

### Verificación de suite de tests
- **Comando:** `.venv/bin/pytest --tb=no -q`
- **Resultado:** 96 passed, 0 failed (idéntico a las 3 noches anteriores)
- Suite intacta. Sin cambios de código esta noche.

### Triage
- Inbox: vacío (ningún archivo nuevo).
- No hay contexto activo nuevo del día para PSA.
- Sin nuevas tareas generadas.

### Wiki actualizada
- `wiki/INDEX.md`: fecha actualizada a 2026-09-10; bloqueo corregido — ahora documenta las
  DOS causas independientes (pre-registro incompleto + entorno SWE-bench no configurado),
  no solo la de API budget. Esto es más preciso que las noches anteriores.

---

## Atascado / Fallas

### Noche sin producción nueva (4ª consecutiva)

Las 3 tareas de código siguen bloqueadas. Diagnóstico más preciso que noches anteriores:

| tarea | bloqueante 1 | bloqueante 2 |
|---|---|---|
| Piloto de banda informativa | Pre-registro: 2 campos sin llenar (band + seeds) | Entorno SWE-bench no configurado |
| Corrida de controles | Pre-registro: 2 campos sin llenar (model + seeds) | Entorno SWE-bench no configurado |
| Corrida piloto completa | Bloqueada por las dos anteriores | — |

**El bloqueo de API budget es SECUNDARIO.** Incluso con autorización de gasto, los runs no
podrían ejecutarse porque:
1. Ejecutar con campos `[PENDIENTE HUMANO]` en el pre-registro viola su propósito: los
   parámetros se fijan ANTES de ver resultados. Correr sin ellos convierte el estudio en no
   pre-registrado.
2. `ClaudeCodeRunner` corre el CLI de Claude Code sobre tareas SWE-bench que requieren un
   entorno de evaluación (docker/VM por tarea) que no está configurado en este equipo.

---

## Decisiones pendientes (para Joel) — urgente

**4ª noche consecutiva. El sistema NOCHE no puede avanzar sin estas resoluciones.**

Las 4 del pre-registro (llenar en `preregistration/run-0-pilot.md` y recommitear):

1. **Band thresholds** — umbrales inferior y superior del filtro de banda informativa.
   Sugerido: 0.10 – 0.90. DEBE fijarse aquí antes del piloto.

2. **Modelo** — identificador exacto del modelo a usar, e.g. `claude-sonnet-5-20251001`.

3. **Seeds** — lista fija de semillas, e.g. `[0, 1, 2]`. Fijadas aquí para que no puedan
   elegirse después de ver resultados.

4. **k y repeticiones por celda** — k determina 2^k configuraciones en la etapa exacta
   (k=7 → 128, k=8 → 256). Repeticiones determinan el poder estadístico y el costo total.

Más la infraestructura (no es decisión, es trabajo técnico que requiere humano):

5. **Entorno SWE-bench** — configurar el entorno de evaluación (docker/VM) para que
   `ClaudeCodeRunner` pueda correr. Sin esto, ninguna corrida es posible.

Y la de nombre:

6. **PSA vs. PCS** — confirmar antes de cualquier referencia externa. (Ver [[pendiente-nombre]])

---

## Entregables

| artefacto | ruta | estado |
|---|---|---|
| Runner real | `psa/runner/claude_code.py` | listo, 18 tests verdes |
| Suite completa | `tests/` | 96 passed (verificado 2026-09-10) |
| Pre-registro piloto | `preregistration/run-0-pilot.md` | borrador — 4 campos abiertos |
| Wiki PSA | `wiki/INDEX.md` | actualizada 2026-09-10 (bloqueo corregido) |
