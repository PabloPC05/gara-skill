---
name: "gara-retro"
description: "Analiza el historial real de uno o varios trabajos Gara (git, REVISION.md, TAREAS.md, correcciones) para proponer cambios concretos a sus skills; usar tras entregar o cuando un patrón de fallos se repite."
disable-model-invocation: true
---

# Retrospectiva Gara

Lee el [perfil Gara](references/gara.md) y el [flujo manual](references/flujo.md). Ejecución directa, sin agentes. Solo lees: no edites skills, artefactos ni código.

## Pasos

1. Acota el periodo o los `specs/<slug>/` que el usuario indique. Si no lo ha dicho, pregunta.
2. Reúne la evidencia real: `git log` y `git diff` del periodo (en especial commits de corrección, `fix` o reversiones tras una fase), `TAREAS.md` (tareas con `Evidencia` de fallos o reintentos, bloqueadas, con aceptación débil), `REVISION.md` (hallazgos por severidad, limitaciones, repeticiones de verify/review sobre SHA nuevos) y `## Bloqueado` resueltos. Los contratos de [artefactos](references/artifacts.md) dicen dónde está cada dato.
3. Busca patrones con ejemplos citados (ruta, commit, tarea): requisitos ambiguos que acabaron en rehacer trabajo, aceptaciones que no detectaron un fallo que luego apareció, hallazgos recurrentes, fases que se saltaron o se repitieron. Distingue hechos, mediciones e inferencias; no extraigas una regla universal de un incidente aislado.
4. Propón cambios acotados a una skill, agente o contrato concretos, cada uno con su evidencia, el efecto esperado y cómo comprobar después si funcionó. Si faltan datos, limita la conclusión y lista lo pendiente. No supongas modelos, precios ni límites vigentes: consúltalos en fuentes oficiales si los necesitas.

## Parada

Termina aquí; no apliques las propuestas. Devuelve: resumen del periodo analizado, hallazgos con su evidencia, propuestas priorizadas, datos que faltaron y decisión pendiente del usuario sobre cuáles aplicar (el cambio lo harás solo si lo pide).

## Referencias

- [artifacts.md](references/artifacts.md)
- [flujo.md](references/flujo.md)
