---
name: "gara-workflow"
description: "Guía manual del flujo Gara: qué skills y agentes usar en cada caso (feature, bug, interfaz, investigación…), orden de fases, puntos de control y cómo retomar un trabajo leyendo specs/<slug>/ y git; usar cuando el usuario no sepa qué invocar para un trabajo, por qué fase va o qué sigue. No ejecuta ninguna fase."
disable-model-invocation: true
---

# Flujo Gara

Lee el [perfil Gara](references/gara.md) y el [flujo manual](references/flujo.md), que es la fuente de las reglas y de la tabla de fases. Esta skill orienta; no lanza fases, no escribe artefactos ni código.

## Orden

`gara-spec` → `gara-plan` → `gara-tasks` → `gara-build` (una tanda por invocación) → `gara-probar` (si el cambio se ve en la app) → `gara-verify` → `gara-review` → `gara-deliver`. Cada una la invoca el usuario y termina con una parada. Una corrección pequeña y acotada puede saltarse spec, plan y tareas si el usuario lo pide, con aceptación proporcional y `gara-commit`.

## Elegir skills y agentes

Para decidir qué invocar según el tipo de trabajo, si hace falta issue y qué agentes pueden intervenir, usa los [casos de uso](references/casos-de-uso.md). Recomienda el caso que encaje y explica por qué; si no encaja ninguno, dilo.

## Retomar un trabajo

Sin depender de la conversación, lee solo lo necesario:

1. `git branch --show-current`, `git status` y `git log --oneline -10`: rama (¿coincide con el issue?), cambios sin commitear y último trabajo.
2. `specs/<slug>/`: qué archivos existen y su contenido; los artefactos están descritos en [artifacts.md](references/artifacts.md).
3. Deduce la fase actual: sin `SPEC.md` o con `approved: false` → `gara-spec`; SPEC aprobada sin `PLAN.md` → `gara-plan`; sin `TAREAS.md` → `gara-tasks`; tareas `pendiente`, `en curso` o `bloqueada` → `gara-build`; todas `verificada` sin Verificación → `gara-verify`, precedida de `gara-probar` si el cambio tiene interfaz y el usuario no lo ha probado aún en el navegador; sin Revisión → `gara-review`; revisión cerrada sin `ENTREGA.md` → `gara-deliver`.
4. Busca `## Bloqueado` en los artefactos y comprueba que el SHA de `REVISION.md` coincide con HEAD y que no hay cambios posteriores; si no, verificación y revisión están obsoletas.

## Parada

Devuelve: slug y rama, fase deducida con la evidencia que la sostiene, bloqueos o incoherencias (por ejemplo, tareas `en curso` tras una interrupción: comprobar qué quedó hecho antes de repetir) y la fase que el usuario podría invocar. Si hay ambigüedad, pregunta; no avances ni invoques la fase.

## Referencias

- [artifacts.md](references/artifacts.md)
- [casos-de-uso.md](references/casos-de-uso.md)
- [delegation.md](references/delegation.md)
- [flujo.md](references/flujo.md)
