---
name: "gara-plan"
description: "Diseña la arquitectura y la validación de una SPEC aprobada de Gara; usar justo antes de dividir el trabajo en tareas, o cuando haya que rehacer PLAN.md tras un cambio de requisitos."
disable-model-invocation: true
---

# Plan técnico Gara

Lee el [perfil Gara](references/gara.md), el [flujo manual](references/flujo.md) y aplica las instrucciones del checkout objetivo. Solo escribe `specs/<slug>/PLAN.md`.

## Pasos

1. Comprueba que la SPEC tiene `approved: true` y no tiene `## Bloqueado`. Si no, para y dilo.
2. Lee la SPEC y el código actual: módulos afectados, tipos, consumidores, tests y configuración. Contrasta los supuestos con HEAD; un baseline histórico no describe el checkout.
3. Delega solo si compensa, según el [contrato de delegación](references/delegation.md): `gara-scout` para módulos y consumidores, `gara-researcher` para una pregunta técnica externa concreta. Sin agentes, explora y consulta documentación primaria tú; si falta acceso a una fuente necesaria, registra el supuesto pendiente.
4. Escribe el plan según el [contrato de artefactos](references/artifacts.md): contratos literales, estados y errores, restricciones, fuera de alcance, integración y traducción de cada aceptación a una prueba o comando real. Los cambios de esquema incluyen modelo y migración Alembic; los plugins respetan su SDK público; en frontend, señala los flujos que requieren comprobación visual contra los tokens existentes.
5. Resuelve las dudas técnicas explorando; una decisión material de producto vuelve al usuario. Ante un supuesto falso, escribe `## Bloqueado`.

No implementes, no dividas en tareas ni toques la SPEC. Si cambian requisitos o arquitectura tras construir, documenta una versión nueva del plan.

## Parada

Termina aquí; no generes `TAREAS.md`. Devuelve: resumen del plan, archivo escrito, decisiones pendientes y siguiente fase sugerida: `/gara-tasks` cuando el usuario acepte el plan.

## Referencias

- [artifacts.md](references/artifacts.md)
- [delegation.md](references/delegation.md)
- [flujo.md](references/flujo.md)
