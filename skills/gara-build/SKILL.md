---
name: "gara-build"
description: "Implementa una tanda de tareas de TAREAS.md de Gara, ejecuta su aceptación y registra la evidencia; usar solo cuando el usuario ya revisó TAREAS.md y pide construir, y se detiene tras cada tanda."
disable-model-invocation: true
---

# Construcción Gara

Lee el [perfil Gara](references/gara.md), el [flujo manual](references/flujo.md) y aplica las instrucciones del checkout objetivo. Escribe código dentro de los archivos propios de cada tarea y actualiza `Estado` y `Evidencia` en `TAREAS.md`; nada más.

## Pasos

1. Comprueba antes de tocar nada: SPEC aprobada, `TAREAS.md` sin `## Bloqueado` y revisado por el usuario, rama e issue conforme al perfil (si no puedes acreditarlos, para) y `git status` para conservar cambios ajenos. Los comandos de aceptación los ejecutas tú: si alguno toca algo fuera del alcance o es dudoso, no lo lances y pregunta.
2. Elige la siguiente tanda con tareas `pendiente` cuyas dependencias estén `verificada` (o la que pida el usuario). Marca cada tarea `en curso`.
3. Implementa cada tarea en esta sesión o, si compensa, delega la tarea íntegra en `gara-implementer` según el [contrato de delegación](references/delegation.md). Lo que devuelve un implementador no es evidencia: tú ejecutas la aceptación.
4. Ejecuta cada comando de aceptación tal como está escrito y copia a `Evidencia` el comando, el código de salida y un resumen real (recortado y sin secretos). Pasa a `verificada` solo si la aceptación se ejecutó y pasó. Si falla, la tarea queda `en curso` con el fallo registrado; no cambies pruebas ni la aceptación para ponerlas en verde. Si falta una decisión o permiso, `bloqueada` con `## Bloqueado`, y sigue solo con lo independiente.
5. No amplíes el alcance. No hagas commit, push ni cambios en Linear: eso es del usuario (commit con `gara-commit` y solo bajo orden suya). Tras una interrupción, comprueba qué quedó hecho antes de repetir; un envío HPC incierto nunca se reenvía por deducción.

## Parada

Para al terminar la tanda, aunque queden tareas, o antes si hay un `Punto de revisión: sí`. Devuelve: resumen, archivos tocados, `git diff --stat` y el diff de la tanda, comandos lanzados con su salida real, estados de cada tarea, decisiones pendientes y siguiente paso sugerido: otra `/gara-build` para la siguiente tanda, `/gara-commit` si el usuario quiere registrar, o `/gara-verify` si no quedan tareas pendientes.

## Referencias

- [artifacts.md](references/artifacts.md)
- [delegation.md](references/delegation.md)
- [flujo.md](references/flujo.md)
