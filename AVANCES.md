# AVANCES — PSA — noche 2026-09-11

## Hecho

### Verificación de suite de tests
- **Comando:** `.venv/bin/pytest --tb=no -q`
- **Resultado:** 96 passed, 0 failed (5ª noche consecutiva idéntico)
- Suite intacta. Sin cambios de código esta noche.

### Triage
- Inbox: vacío.
- No hay contexto activo nuevo del día para PSA.
- Sin nuevas tareas generadas.

### Wiki actualizada
- `wiki/INDEX.md`: fecha actualizada a 2026-09-11; bloqueo ascendido a 5ª noche consecutiva.
  Sin conocimiento nuevo — el diagnóstico no cambió.

---

## Atascado / Fallas

### Noche sin producción nueva (5ª consecutiva)

Las 3 tareas de código siguen bloqueadas. Diagnóstico sin cambio:

| tarea | bloqueante 1 | bloqueante 2 |
|---|---|---|
| Piloto de banda informativa | Pre-registro: 2 campos sin llenar (band + seeds) | Entorno SWE-bench no configurado |
| Corrida de controles | Pre-registro: 2 campos sin llenar (model + seeds) | Entorno SWE-bench no configurado |
| Corrida piloto completa | Bloqueada por las dos anteriores | — |

---

## Decisiones pendientes (para Joel) — 5ª noche sin respuesta

Sin estas resoluciones el sistema NOCHE no puede avanzar:

Las 4 del pre-registro (llenar en `preregistration/run-0-pilot.md` y recommitear):

1. **Band thresholds** — umbrales inferior y superior del filtro de banda informativa.
   Sugerido: 0.10 – 0.90. DEBE fijarse antes del piloto.

2. **Modelo** — identificador exacto, e.g. `claude-sonnet-5-20251001`.

3. **Seeds** — lista fija, e.g. `[0, 1, 2]`. Deben fijarse antes de ver resultados.

4. **k y repeticiones por celda** — k determina 2^k configuraciones (k=7 → 128, k=8 → 256).

Más la infraestructura (trabajo técnico, requiere humano):

5. **Entorno SWE-bench** — configurar docker/VM para que `ClaudeCodeRunner` pueda correr.

Y el nombre:

6. **PSA vs. PCS** — confirmar antes de cualquier referencia externa. (Ver [[pendiente-nombre]])

---

## Entregables

| artefacto | ruta | estado |
|---|---|---|
| Runner real | `psa/runner/claude_code.py` | listo, 18 tests verdes |
| Suite completa | `tests/` | 96 passed (verificado 2026-09-11) |
| Pre-registro piloto | `preregistration/run-0-pilot.md` | borrador — 4 campos abiertos |
| Wiki PSA | `wiki/INDEX.md` | actualizada 2026-09-11 |
