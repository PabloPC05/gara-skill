# Flujo manual Gara

Tú diriges el trabajo. No hay ejecutor automático: cada fase es una skill que invocas tú (`/gara-spec`, `/gara-plan`, …) y ninguna fase lanza la siguiente.

## Reglas de control

- **Una fase por invocación.** Al terminar, la skill se detiene y devuelve: qué hizo, qué archivos tocó, qué decisiones esperan al usuario y cuál sería el siguiente paso. No encadena fases ni "aprovecha" para adelantar trabajo.
- **Aprobar es explícito.** `approved: true` en la SPEC, el visto bueno a `TAREAS.md` antes de construir y la orden de commit o publicación son decisiones del usuario. El silencio, un "ok, sigue" ambiguo o una petición de analizar no las conceden.
- **Nada irreversible sin orden.** Commits (solo con `gara-commit`), push, PR, cambios de estado en Linear y cualquier acción sobre servicios externos requieren una petición concreta del usuario en ese momento.
- **Sin estado oculto.** La verdad está en `specs/<slug>/` y en Git. Para retomar un trabajo, lee esos archivos y `git status`/`git log`; no dependas de la memoria de la conversación.
- **Si falta algo, para.** Una decisión de producto, un permiso o un dato ausente se registra con `## Bloqueado` en el artefacto y se pregunta; no se rellena con suposiciones.

## Fases

| Fase | Entrada | Salida | Antes de pasar a la siguiente |
| --- | --- | --- | --- |
| `gara-spec` | petición, issue | `SPEC.md` | el usuario pone `approved: true` |
| `gara-plan` | SPEC aprobada | `PLAN.md` | el usuario lee el plan y lo acepta |
| `gara-tasks` | SPEC + PLAN | `TAREAS.md` | el usuario revisa tareas y comandos de aceptación |
| `gara-build` | `TAREAS.md` revisado | código + estados en `TAREAS.md` | el usuario revisa el diff de cada tanda |
| `gara-probar` (recomendada si el cambio se ve en la app) | código construido y app arrancada | resultado por escenario con capturas | el usuario decide si vuelve a `gara-build` o sigue |
| `gara-verify` | código construido | sección Verificación de `REVISION.md` | el usuario lee los hallazgos |
| `gara-review` | código verificado | sección Revisión de `REVISION.md` | el usuario decide qué corregir o aceptar |
| `gara-deliver` | revisión cerrada | `ENTREGA.md`, PR | el usuario autoriza publicar |

Ajusta la profundidad al trabajo: una corrección pequeña y acotada puede saltarse spec, plan y tareas si el usuario lo pide, manteniendo aceptación proporcional y `gara-commit`.

## Puntos de control

- **Tras `gara-tasks`**: los comandos de aceptación los ejecutará `gara-build` en tu máquina con tus permisos. Léelos antes de construir; deben poder fallar y no tocar nada fuera del alcance.
- **Tras cada tanda de `gara-build`**: la skill se detiene aunque queden tareas, con el diff, los comandos lanzados y su salida real. Continúa solo cuando lo pidas.
- **Al terminar de construir**: si el cambio se ve en la app, recórrelo con `gara-probar` antes de verificar; los fallos que encuentre se corrigen con otra tanda de `gara-build`. Si el cambio es solo backend o lógica sin interfaz, las aceptaciones bastan y se pasa directamente a `gara-verify`.
- **Tareas con `Punto de revisión: sí`**: comprobación humana concreta (pantalla, flujo, dato) antes de seguir.
- **Antes de `gara-deliver`**: la revisión de un agente no equivale a la revisión humana que Gara exige para `Done`.

## Cambios durante el trabajo

Un cambio en SPEC o PLAN después de construir abre una versión nueva (documenta qué cambió y por qué); no reescribas el historial para ocultarlo. Si tras verify o review cambia el código, la verificación y revisión previas dejan de valer para el nuevo SHA y se repiten las afectadas. Tras una interrupción, comprueba qué quedó hecho (`git status`, tareas marcadas) antes de repetir; un envío HPC incierto nunca se reenvía por deducción.

## Permisos y secretos

Los modelos y permisos son los de tu sesión de Claude Code; las skills no añaden bypasses ni amplían permisos, servidores o configuración global. Nunca incluyas credenciales ni contenido de `.env` en briefings, logs o artefactos. La salida de comandos que copies a `TAREAS.md` o `REVISION.md` se recorta y se revisa antes por si contiene tokens.

## Instalación

Copia `skills/*` a `~/.claude/skills/` y `agents/*` a `~/.claude/agents/` (o a `.claude/` de un proyecto para limitarlo a él) y abre una sesión nueva. Los archivos de `references/` de cada skill son copias de `references/` y `profiles/gara.md` del repositorio; modifica siempre el original y vuelve a copiar.

## Fuentes

- [Skills de Claude Code](https://code.claude.com/docs/en/skills).
- [Agentes de Claude Code](https://code.claude.com/docs/en/sub-agents).
