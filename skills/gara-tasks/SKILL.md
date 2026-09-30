---
name: "gara-tasks"
description: "Transforma PLAN.md y SPEC.md de Gara en un contrato TAREAS.md ejecutable, con cobertura de requisitos, dependencias y tandas."
---

# Tareas Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe SPEC, PLAN, rutas reales y capacidades del entorno; entrega `TAREAS.md` con briefings completos, ownership, dependencias y aceptación. Esta skill programa el trabajo: no lanza implementadores. El mismo contrato permite a gara-build trabajar secuencialmente cuando no haya delegación.

Lee el plan completo y copia en cada briefing los contratos que necesita su implementador. Cada tarea declara ID, requisitos, dependencias, archivos concretos, resultados, aceptación y estado. No inventes arquitectura ni modifiques el plan.

Escribe el bloque gara-tasks:v1 del contrato de artefactos. Todas las R de la SPEC quedan cubiertas por aceptación ejecutable. Usa rutas reales, argv sin shell y directorios de trabajo explícitos. No sustituyas una comprobación de comportamiento por un comando que siempre sale con éxito.

Programa contratos y pruebas de interfaz entre módulos antes que sus consumidores. Ordena por dependencias, colisiones y recursos; prioriza riesgo en tareas independientes. Cada tanda tiene hasta tres tareas, carga máxima 4 y ningún escritor sobre los mismos archivos. Adapta el paralelismo a las capacidades y límites del entorno; un entorno sin subagentes trabaja secuencialmente.

Si el plan omite una decisión necesaria, documenta el hueco y bloquea lo dependiente. Los checkpoints señalan una comprobación humana concreta. Una revisión visual cierra el bloque de frontend cuando la pantalla completa ya existe.

## Referencias

- [artifacts.md](references/artifacts.md)
- [runtime.md](references/runtime.md)
