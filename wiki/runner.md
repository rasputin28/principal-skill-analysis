# Runner

La frontera de sustitución del arnés. Toda comparación entre autores requiere que el arnés sea
sustituible: cualquier harness soportado es una implementación del protocolo `Runner`.

## Protocolo (psa/runner/base.py)

```python
class Runner(Protocol):
    name: str
    model: str
    def run(task_id, workspace, skills_assigned, seed) -> RunOutcome: ...
```

`RunOutcome` campos obligatorios: `resolved`, `f2p_fraction`, `turns`, `tokens`,
`wall_seconds`, `skills_invoked`. El último es el contrato crítico: deben ser las skills
**realmente invocadas**, no solo las asignadas. La diferencia es el análisis ITT vs. tratados.

## ClaudeCodeRunner (psa/runner/claude_code.py)

Implementado 2026-09-07 en rama `noche/2026-09-07-runner`.

- Llama al CLI `claude` vía subprocess
- Pasa `CLAUDE_SKILLS_DIR=workspace` para que el CLI cargue skills del workspace hermético
- Parsea `--output-format json` del transcript para extraer llamadas a `Skill` tool
- `skills_invoked` = skill IDs de llamadas `{"type":"tool_use","name":"Skill","input":{"skill":"..."}}`

### HarnessUnsupported

Se lanza (en lugar de devolver datos silenciosamente incorrectos) cuando:
- Binary `claude` no está en PATH
- La corrida excede timeout
- El proceso devuelve código de salida ≠ 0
- El transcript no tiene clave `"messages"` (no se puede determinar qué skills se invocaron)
- El transcript no es JSON válido

### StubRunner

Existente en `base.py`. Devuelve hashes deterministas, NO mediciones. `report.guard()` rechaza
cualquier ledger que contenga registros de este runner. Existe únicamente para tests de cableado.

## Invocación vs. asignación

| término | significado |
|---|---|
| `skills_assigned` | la configuración: qué skills estaban disponibles en el workspace |
| `skills_invoked` | las skills que el agente realmente leyó (vía Skill tool) |

La diferencia define el análisis ITT (intention-to-treat) vs. tratados. Ambos se reportan;
la brecha es el control 7.2 del diseño. Ver [[design]].
