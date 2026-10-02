# Auditoría de skills y workflow (2 de octubre de 2026)

Segunda auditoría, posterior a [A01–A10](corrections.md). Cubre las 29 skills frente a `catalog.json`, los roles y los contratos compartidos, y el ejecutor `gara_workflow/`. Método: tres lecturas independientes del repositorio (skills, runtime, auditoría previa) y comprobación directa en el código de los hallazgos más graves. Las pruebas se ejecutaron en Windows con Python 3.13; Linux y macOS no se probaron localmente.

Estados: **corregido** (con prueba de regresión), **documentado** (el comportamiento queda descrito, sin cambio de código), **abierto** (no se ha tocado) y **sospecha** (plausible, no reproducida).

## Modelo de confianza de las aceptaciones

El hallazgo de mayor alcance no es un fallo puntual, sino un límite que la documentación presentaba de forma optimista. El modelo escribe `acceptance.argv` en `TAREAS.md` y el coordinador lo ejecuta **fuera del sandbox del cliente**, con permisos de usuario y, hasta ahora, con el entorno completo. «argv, no shell» evita la interpolación, pero no impide `sh -c`, `python -c` ni `curl`. Se mantiene el modo automático, pero ya no sin revisión humana ni sin acotar el alcance (R1, R2). Sigue sin ser un sandbox: está dicho así en [runtime.md](../../references/runtime.md).

## Runtime

| ID | Hallazgo | Estado |
| --- | --- | --- |
| R1 | Gates con `os.environ` completo, sin tope de timeout y con aceptaciones que no pueden fallar (`python -c pass`, `true`) | Corregido: entorno mínimo (`GATE_ENVIRONMENT`), timeout 1–3600 s, rechazo heurístico de aceptaciones triviales. La heurística no demuestra que una prueba sea buena |
| R2 | Un contrato podía nacer con tareas `verified`/`running` y saltarse la implementación; sin pausa humana si todas llevaban `checkpoint:false` | Corregido: un contrato nuevo exige todo `pending` y el flujo se detiene tras `tasks` hasta `--ack-checkpoint`. **Cambia el uso del modo automático**: se puede dar `--ack-checkpoint` desde el primer `run` |
| R3 | `redact` no cubría `Authorization: Token/Basic`, `*_SECRET_KEY`, credenciales en URL, `ghp_`/`AKIA`/JWT ni PEM; recortaba antes de redactar; `argv` sin redactar | Corregido. Un secreto con formato desconocido, o un valor con espacios tras una clave, sigue sin detectarse (**abierto**) |
| R3b | La evidencia de los gates se escribe en `TAREAS.md` (versionado), no en el directorio Git privado como decía `runtime.md` | Documentado |
| R4 | `inside()` no protegía `.git` en Windows (`.git.`, `.git `, `GIT~1`), reproducido por el explorador | Corregido. Los contratos además prohíben `.claude/`, `.codex/`, `.husky/` y `.env*` |
| R5 | Con varios marcadores `gara-result` ganaba el primero (contenido citado podía forjar `completed`); falsos positivos de autenticación y de `429` | Corregido: gana el último marcador, un resultado `completed` no se bloquea por citar «please run /login» y `429`/`529` van delimitados |
| R6 | Sin tratamiento de SIGTERM/SIGHUP; `killpg` sin proteger enmascaraba el error original; sin SIGKILL a descendientes | Corregido (señal → interrupción 130 con estado guardado; limpieza que no lanza). **Abierto**: no se persiste el PID del cliente y una muerte forzada deja un posible huérfano sin lock (documentado) |
| R7 | Sin salida tras merge/rebase de la rama base; checkpoints ya confirmados sobrevivían a una reconstrucción; excepciones no previstas dejaban `running` | Corregido: `reset --slug S --yes`, checkpoints limpiados al degradar, estado `failed` para fallos no previstos |
| R8 | `changes()` ignora archivos ignorados (`.venv`, `.git/hooks`) fuera de publish; `resolve_command` ejecuta el `.venv` del checkout | **Abierto** |
| R8b | `git` invocado sin ruta absoluta (Windows busca en el directorio actual) | **Sospecha**, no reproducida |
| R9 | `pdf --keep-html` pisaba el contenido de entrada | Corregido |
| R9b | `Bloqueado` se detectaba de dos formas distintas | Corregido (misma expresión que `specification`) |
| R9c | `install` no es atómico; `TASK_BLOCK` toma el primer bloque; `redact` O(n²) | **Abierto**, prioridad baja |

## Skills y catálogo

| ID | Hallazgo | Estado |
| --- | --- | --- |
| S1 | Reglas incompatibles de movimiento entre `gara-ui-animation`, `gara-fixing-motion-performance` y `gara-baseline-ui` (blur 20 px frente a 8 px, layout, Motion por defecto frente a prohibido) | Corregido: 8 px, layout solo en superficies pequeñas medidas, Motion solo si el checkout ya lo usa |
| S2 | `gara-commit` y `gara-find-skills` eran invocables de forma implícita | Corregido: `explicit_only: true` (17 skills explícitas). El ejecutor no se ve afectado: lee `SKILL.md` por ruta |
| S3 | `gara-diseno` citaba un flag `--default` inexistente y «el monocromo de OSIX» | Corregido |
| S4 | `gara-retro`, `gara-workflow-setup` y `gara-workflow-health` usaban `metrics`, `doctor` y términos de `artifacts.md` sin llevar esos contratos | Corregido |
| S5 | `gara-deliver` omitía la línea `Implementation SHA:` y la congelación; `gara-review` describía `REVISION.md` como informe libre | Corregido |
| S6 | `gara-verify` mandaba commitear sin condicionar a autorización | Corregido |
| S7 | `## Bloqueado` solo documentado para SPEC | Corregido en `artifacts.md` |
| S8 | Descripciones con «usar para el comportamiento concreto descrito» en cuatro skills | Corregido. Cuerpos en inglés de esas skills: **abierto** (se conservan por ser material adaptado) |
| S9 | `gara-build` omitía `In Progress`; ejemplo Next.js en `gara-fixing-metadata`; restos de iOS/Apple en `gara-ui-animation` | Corregidos los dos primeros; el tercero **abierto** |
| S10 | Las copias de `profiles/` y `references/` versionadas dentro de cada skill no se comprobaban. El resultado de `build` sí se refresca desde las fuentes (lo fija un test existente), pero quien lee una skill desde el checkout, como hace el ejecutor sin instalación, ve la copia versionada | Corregido con un test sobre el repo real. `validate` **no** rechaza copias viejas: un primer intento chocó con ese contrato y se retiró |

Comprobado y correcto: catálogo, matriz de delegación y texto de cada skill coinciden (21 directas, 8 coordinadas); no hay enlaces rotos; las 54 copias estaban idénticas antes de esta auditoría; no hay rutas personales en skills, roles ni referencias.

## Repositorio e integración continua

- Rutas personales (`C:\Users\...\.codex`) en `docs/audit/installation*.json`: sustituidas por `~`.
- CI pasa a Ubuntu con Python 3.11 y 3.12 y Windows con 3.12. **No se ha podido ejecutar en GitHub desde aquí**: el primer resultado remoto es la verificación pendiente.
- Las skills `gara-commit` y `gara-find-skills` cambian de política; la cifra de «15 políticas explícitas» de [validation.md](../validation.md) era la de la exportación original.

## Pendiente

R6 (PID), R8, R8b, R9c, secretos con formato desconocido, cuerpos en inglés y restos iOS en `gara-ui-animation`. Tampoco se han evaluado en tareas reales las skills individuales ni los diez roles: esta auditoría revisa su coherencia, no su calidad de salida.
