---
name: "gara-deliver"
description: "Publica la rama revisada de Gara, abre la PR y deja el issue en In Review; usar solo cuando el usuario ordene explícitamente publicar, tras cerrar gara-review."
disable-model-invocation: true
---

# Entrega Gara

Lee el [perfil Gara](references/gara.md), el [flujo manual](references/flujo.md) y aplica las instrucciones del checkout objetivo. Ejecución directa, sin agentes. Solo escribe `specs/<slug>/ENTREGA.md` (contrato en [artifacts.md](references/artifacts.md)).

## Pasos

1. Sin una orden explícita de publicar en este momento, no hagas push, PR ni cambios en Linear: prepara el borrador del cuerpo de la PR y para. Invocar la skill no es esa orden.
2. Con orden, comprueba: issue y rama, `git status` limpio, commits ya hechos (no los crees aquí), `REVISION.md` cerrado sin bloqueos y con el SHA que vas a publicar, documentación afectada y estado de CI para ese SHA. Distingue gates locales de checks remotos vivos. Si algo falla, para y dilo.
3. Reutiliza la PR de la rama si existe; no dupliques. Con las capacidades autenticadas disponibles, publica la rama, abre o actualiza la PR vinculando el issue y pasa el issue a `In Review` con alcance, comandos, resultados y limitaciones. Si usas `gh`, da el cuerpo en un archivo UTF-8 creado fuera del checkout. Si faltan credenciales o conectores, prepara el contenido, registra la acción externa pendiente y no inventes una actualización.
4. Escribe `ENTREGA.md` con la URL de la PR, el estado observado de Linear y `Implementation SHA: <SHA de la revisión>`. Desde ahí, cambiar código o artefactos invalida verify y review.
5. No hagas merge, no muevas a `Done`, no autoapruebes ni despliegues: la revisión de un agente no sustituye la humana.

## Parada

Termina aquí. Devuelve: resumen, archivos tocados, URL de la PR y estado de Linear observados, acciones externas pendientes y decisiones del usuario. Siguiente paso sugerido: revisión humana y merge por su cuenta; `/gara-retro` si quiere una retrospectiva.

## Referencias

- [artifacts.md](references/artifacts.md)
- [flujo.md](references/flujo.md)
