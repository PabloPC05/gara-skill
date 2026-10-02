---
name: "gara-deliver"
description: "Publica una rama verificada de Gara y entrega PR y evidencias a In Review cuando el usuario pide explícitamente publicar o utiliza --publish."
---

# Entrega Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe autorización de publicación, issue/rama, SHA verificado y evidencias de revisión/CI; entrega PR, estado observado de Linear y `ENTREGA.md`. Usa las capacidades autenticadas disponibles en la sesión. Si faltan, prepara el contenido y registra la acción externa pendiente; la ausencia de agentes no impide preparar la entrega.

Comprueba autorización concreta de publicación, issue y rama, commits, documentación, aceptación y estado del CI. Reutiliza la PR de la rama si existe; no dupliques entregas al reanudar.

Con las herramientas autenticadas disponibles, publica la rama y abre o actualiza la PR, vinculando el issue según el proceso canónico. Si usas gh, proporciona el cuerpo mediante un archivo UTF-8 con nuevas líneas reales. Distingue gates locales de checks remotos vivos para el mismo SHA.

Entrega el issue a In Review y deja evidencia del alcance, comandos, resultados y limitaciones mediante las capacidades de Linear disponibles. Si faltan credenciales o conectores, prepara la descripción y registra el bloqueo; no inventes una actualización externa.

Escribe únicamente ENTREGA.md con la URL de la PR, el estado observado de Linear (`In Review`) y la línea literal `Implementation SHA: <SHA de review>`; el código, SPEC, PLAN, TAREAS y REVISION están cerrados y cualquier cambio los invalida. Si necesitas un archivo para el cuerpo de la PR, créalo fuera del checkout. La revisión de agentes no permite autoaprobar el trabajo, hacer merge o moverlo a Done; aplica excepciones solo mediante instrucciones explícitas vigentes del propietario. La invocación de esta skill no autoriza un despliegue.

## Referencias

- [artifacts.md](references/artifacts.md)
- [runtime.md](references/runtime.md)
