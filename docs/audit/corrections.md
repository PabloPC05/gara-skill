# Correcciones de la auditoría

Cambios del 1 de octubre de 2026, implementados con tres subagentes GPT-6.1-Sol, razonamiento `max`, y revisión cruzada independiente. La instalación conserva modelos y permisos heredados.

## Skills y agentes

Las 29 skills declaran entradas, salidas, ejecución y fallback. Ocho coordinan agentes cuando hay trabajo que lo justifica; 21 ejecutan directamente. Los diez roles tienen un caso de uso identificado en la [matriz](../../references/delegation.md). El catálogo valida nombres, referencias y coherencia de ambos modos.

Los roles Claude que usan skills incluyen `Skill`. El revisor visual hereda el conjunto autorizado del cliente para acceder a su navegador; no se configuran servidores MCP. Los diez roles excluyen delegación anidada. Verifier separa conformidad y corrección en contextos nuevos. Baseline UI reutiliza tokens y primitivas de Gara, CSS/WAAPI o infraestructura existente, sin exigir instalar una dependencia de animación.

## Garantías del ejecutor

| Hallazgo | Corrección y comprobación |
| --- | --- |
| A01 | Publish solo escribe `ENTREGA.md`; congela contratos, revisión, código e índice. Detecta nuevos commits, cambios ignorados y modificación seguida de revert. Un cambio prohibido invalida el cierre. |
| A02 | Redacción recursiva de campos estructurados, JSON, cadenas codificadas y formatos textuales detectables; persistencia normalizada sin streams de herramientas. Regresión con comillas dentro del secreto. |
| A03 | Capacidades Claude corregidas y metadatos nativos validados. |
| A04 | `gara-review:v1` exige autor, cobertura, aceptaciones, hallazgos, límites y SHA real de implementación. Verify y review conservan registros separados. Las delegaciones se observan mediante eventos; la independencia sigue declarada como `unverified`. |
| A05 | Contratos de briefing/devolución, selección exacta de roles y fallback proporcional en todas las skills. |
| A06 | Lock de todo el checkout: slugs distintos se excluyen entre procesos; worktrees independientes conservan locks propios. |
| A07 | Baseline coherente con el stack y reduced motion de Gara. |
| A08 | Retirada de obsoletos por motor seleccionado y hash previo. Bloquea ediciones locales antes de escribir; conserva componentes ajenos y legacy. |
| A09 | Identificador completo del issue en la rama; rechaza prefijos numéricos y coincidencias embebidas. |
| A10 | Instalación y dry-run comparten payload y preflight; el preview no escribe `.build` ni destinos y detecta las mismas colisiones. |

La revisión cruzada también corrigió un índice con código roto y worktree restaurado, `publication_sha` obsoleto tras reconstruir, una lista de fases final incorrecta, flags `assume-unchanged`/`skip-worktree` y renombrados de archivos por mayúsculas en Windows. Las pruebas incluyen estas reproducciones.

## Validación y límites

Las regresiones están en [test_runner_regressions.py](../../tests/test_runner_regressions.py), [test_protocols_regressions.py](../../tests/test_protocols_regressions.py) y [test_installation_regressions.py](../../tests/test_installation_regressions.py). Los resultados completos y la instalación quedan en [validation.md](../validation.md); las siete reproducciones originales repetidas quedan en [resolution.json](resolution.json).

```powershell
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python docs/audit/reproduce.py
.venv/Scripts/python scripts/gara_workflow.py validate
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

Las comprobaciones del guard ocurren al regresar el cliente y conservan los cambios bloqueados para su reconciliación. No revierten cambios automáticamente ni prueban que un efecto remoto haya sido evitado. Los clientes simulados verifican contratos locales; no acreditan modelos reales, publicación, CI remoto o aprobación humana. Los informes anteriores sin el contrato nuevo requieren verificación y revisión reales antes de cerrar.

La prueba opcional `docs/audit/native_smoke.py --engine codex` o `--engine claude` llama al cliente autenticado en lectura sobre este paquete, con modelos heredados. Registra respuestas normalizadas y capacidades observadas en `output/validation/native/`; no ejecuta una feature ni entrega trabajo remoto.

`AGENTS.md`, `export.zip`, los originales y el checkout de Gara se conservan. No se publicaron PRs, modificó Linear ni ejecutó HPC o despliegues para estas pruebas.
