---
name: "gara-tasks"
description: "Convierte SPEC.md y PLAN.md aprobados de Gara en TAREAS.md, con cobertura de requisitos, dependencias, tandas y comandos de aceptación; usar tras aceptar el plan y antes de construir."
disable-model-invocation: true
---

# Tareas Gara

Lee el [perfil Gara](references/gara.md), el [flujo manual](references/flujo.md) y aplica las instrucciones del checkout objetivo. Ejecución directa, sin agentes. Solo escribe `specs/<slug>/TAREAS.md`.

## Pasos

1. Comprueba que existen SPEC aprobada y PLAN sin `## Bloqueado`. Si no, para y dilo.
2. Lee el plan completo y escribe `TAREAS.md` con la plantilla Markdown del [contrato de artefactos](references/artifacts.md). Todas las tareas empiezan en `pendiente` y con `Evidencia` vacía.
3. Cada briefing copia los contratos literales que necesita quien construya, sin inventar arquitectura ni modificar el plan. Cada requisito de la SPEC queda cubierto por una aceptación ejecutable.
4. Ordena por dependencias: contratos y pruebas de interfaz antes que sus consumidores. En una misma tanda, hasta tres tareas y ningún archivo propio compartido; prioriza el riesgo entre tareas independientes.
5. Cada aceptación es un comando real que puede fallar, con directorio de trabajo explícito y rutas relativas con `/` (reglas completas en el contrato). Estos comandos los ejecutará `gara-build` en la máquina del usuario: no deben tocar nada fuera del alcance.
6. Marca `Punto de revisión: sí` donde haga falta una comprobación humana concreta; una revisión visual cierra el bloque de frontend cuando la pantalla completa ya existe.
7. Si el plan omite una decisión necesaria, documenta el hueco y bloquea lo dependiente con `## Bloqueado`.

## Parada

Termina aquí; no construyas nada. Devuelve: resumen de tandas y cobertura de requisitos, archivo escrito, los comandos de aceptación para que el usuario los lea, decisiones pendientes y siguiente fase sugerida: `/gara-build` tras su visto bueno a `TAREAS.md`.

## Referencias

- [artifacts.md](references/artifacts.md)
- [flujo.md](references/flujo.md)
