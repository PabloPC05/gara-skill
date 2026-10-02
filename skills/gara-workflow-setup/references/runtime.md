# Operación del ejecutor

Usa Python 3.11 o superior. Desde el checkout del paquete:

```powershell
py scripts/gara_workflow.py doctor --repo C:/ruta/gara
py scripts/gara_workflow.py run --repo C:\ruta\checkout-gara --slug gar-123-mejora --engine codex --dry-run
py scripts/gara_workflow.py run --repo C:\ruta\checkout-gara --slug gar-123-mejora --engine claude
```

En la skill instalada, resuelve `scripts/gara_workflow.py` respecto a su propio `SKILL.md`, no respecto al repositorio objetivo. El helper lleva consigo el runtime; no depende de que `gara-skill` siga en la misma ruta.

## Inicio y fases

La SPEC debe estar autorizada y asociada a un issue. Se necesita un checkout identificado como Gara, la rama del issue y ausencia de cambios previos ajenos. El identificador completo debe coincidir: `GAR-12` no acepta una rama `gar-123-...`. El modo `--dry-run` valida entradas y enumera fases sin escribir, llamar modelos, instalar ni publicar.

`run` encadena plan → tasks → build por tandas → verify → review. Cada fase comienza en una sesión nueva. Tras `tasks` el flujo se detiene para que una persona revise los comandos de aceptación (checkpoint `tasks`); se continúa con `--ack-checkpoint`, que también puede darse desde el primer `run`. Las tandas se validan mediante comandos ejecutados por el coordinador y después se registran con `gara-commit`. Verify y review necesitan la evidencia estructurada de [REVISION.md](artifacts.md), vinculada al SHA de implementación. Una revisión que corrige código exige nueva verificación y revisión. `--publish` añade entrega a PR e `In Review` mediante las capacidades autenticadas del agente; solo puede escribir `ENTREGA.md` y conserva congelados los archivos cerrados.

## Estado y reanudación

El estado y los resúmenes normalizados viven en el directorio Git privado del checkout, bajo `gara-workflow/<slug>/`. `status`, `sessions` y `metrics` permiten inspeccionarlos. La evidencia de cada aceptación (`argv`, código de salida, `stdout` y `stderr` recortados) se escribe en el bloque de `TAREAS.md`, que sí está en el árbol y puede acabar en la PR. Se redactan campos sensibles estructurados y textos con formatos detectables (cabeceras `Authorization`, `*_SECRET_KEY`, credenciales en URL, tokens `ghp_`/`AKIA`/JWT, claves PEM) antes de recortar; un secreto con formato desconocido no se detecta. No se almacenan streams brutos ni prompts de herramientas. Las delegaciones registran solo metadatos observados: pedir un agente o completar el tool de spawn no acredita que ese agente haya terminado. El estado registra `independence: unverified`; la autoría declarada no sustituye la revisión humana.

```powershell
py scripts/gara_workflow.py resume --repo C:\ruta\checkout-gara --slug gar-123-mejora --engine codex
py scripts/gara_workflow.py resume --repo C:\ruta\checkout-gara --slug gar-123-mejora --engine codex --ack-checkpoint
```

La reanudación comprueba identidad, hashes y relación de HEAD. Tras un merge o rebase de la rama base, los archivos que trae quedan fuera del alcance y bloquean la ejecución; reconcilia el checkout y usa `reset --slug <slug> --yes` (borra solo el estado privado, no `specs/`) para reiniciarla. Un fallo no previsto del ejecutor se guarda como `failed`. Las tareas interrumpidas se contrastan con su aceptación antes de repetir la implementación. Un cambio de contrato bloquea la reutilización de evidencia. Si cambia una entrega ya cerrada, su hash invalida solo publish y conserva las revisiones válidas. Reconstruir código elimina el SHA de publicación anterior. `--resume-session` solo reutiliza una última sesión de revisión correspondiente; el resto de fases conserva el contexto fresco.

El proceso usa un lock por checkout en `git rev-parse --git-path gara-workflow/flow.lock`, liberado por el sistema operativo incluso tras un crash. Dos slugs del mismo checkout no ejecutan escritores simultáneos; worktrees independientes usan locks diferentes. Un fallo de infraestructura se reintenta una vez únicamente cuando no ha cambiado el checkout. Una cuota sin progreso se registra como fallo recuperable; reanuda cuando la cuenta permita trabajar. No se asume una ventana universal de cinco horas.

Salidas: 0 completado o dry-run, 2 bloqueado, 1 fallo, 130 interrupción. SIGTERM, SIGHUP y SIGBREAK se tratan como interrupción: se detiene el grupo de procesos del cliente y se guarda el estado. Una muerte forzada (SIGKILL, cierre de la consola en Windows) no puede hacerlo: el cliente podría seguir escribiendo sin lock y debes comprobarlo antes de reanudar. `--timeout` limita cada sesión, `--retry-infra` controla reintentos y los timeouts de aceptación se declaran en cada tarea.

## Clientes y permisos

Se reutiliza la autenticación de los clientes. Los modelos y permisos se heredan de su configuración. El ejecutor no añade bypasses de permisos a las sesiones del cliente y rechaza tres flags conocidos en `args`. Las aceptaciones de `TAREAS.md` son otra cosa: las lanza el coordinador, fuera del sandbox del cliente y con tus permisos de usuario. Por eso las escribe el modelo pero las revisa una persona (checkpoint `tasks`), se ejecutan con un entorno mínimo (`PATH`, directorios de usuario y temporales, localización; no `GH_TOKEN`, claves de API ni `GIT_*`) y su timeout no supera 3600 s. Esto limita el alcance, no es un sandbox. Si el cliente no autoriza una operación, devuelve el bloqueo para resolverlo en el entorno real.

Configuración opcional en TOML, seleccionada con `--config`:

```toml
[codex]
client = "codex"
args = []

[claude]
client = "claude"
args = []

[pdf]
# browser = "C:/ruta/chrome.exe"
```

Las rutas se pueden configurar; no hay servidor, token o usuario fijo. `watch --host usuario@host --remote-state /ruta/state.json` observa un estado por SSH sin iniciar trabajo remoto. `fixes` recoge evidencias del historial Git sin atribuir categorías automáticamente.

## Fuentes de compatibilidad

- [Skills de Codex](https://learn.chatgpt.com/docs/build-skills).
- [Agentes de Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- [Codex no interactivo](https://learn.chatgpt.com/docs/non-interactive-mode).
- [Skills de Claude Code](https://code.claude.com/docs/en/skills).
- [Agentes de Claude Code](https://code.claude.com/docs/en/sub-agents).
- [Claude Code no interactivo](https://code.claude.com/docs/en/headless).
