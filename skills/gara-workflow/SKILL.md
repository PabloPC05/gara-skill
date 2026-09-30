---
name: "gara-workflow"
description: "Opera o diagnostica el flujo Gara de requisitos, plan, tareas, construcción, verificación y revisión, en modo manual o automatizado."
---

# Flujo Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes propios: recibe checkout, slug, modo solicitado y autorización vigente; entrega estado del ejecutor, artefactos y límites observados. Cada fase seleccionada decide su coordinación mediante el [contrato de delegación](references/delegation.md). No precargues fases explícitas en agentes ni lances otro CLI dentro de un trabajador. Sin delegación, las fases ejecutan el mismo alcance secuencialmente.

El flujo guiado es gara-spec → gara-plan → gara-tasks → gara-build → gara-verify → gara-review. Ajusta su profundidad al trabajo; una corrección claramente acotada puede ejecutarse directamente con aceptación proporcional.

Para automatización, lee la referencia de operación y el contrato de artefactos. Resuelve `scripts/gara_workflow.py` respecto a esta skill. Empieza por doctor y un dry-run; run ejecuta la SPEC autorizada desde una rama de issue. No interpretes una petición de explicar o preparar como una orden de lanzar el flujo.

Un estado completed corresponde a una ejecución local validada. Publicación y entrega se añaden con --publish explícito. Status, metrics, sessions y watch observan el progreso; resume reconcilia hashes y trabajo interrumpido. Usa --ack-checkpoint solo tras una comprobación humana real.

Los clientes, modelos y permisos se heredan de la configuración vigente. No añadas bypasses, servidores, tokens ni modelos fijos. Ante infraestructura fallida después de cambios, reconcilia antes de repetir. Un requisito material pendiente produce un bloqueo documentado.

## Referencias

- [artifacts.md](references/artifacts.md)
- [runtime.md](references/runtime.md)
