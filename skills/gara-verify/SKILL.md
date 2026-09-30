---
name: "gara-verify"
description: "Verifica una implementación de Gara contra SPEC, PLAN y TAREAS, ejecutando criterios de aceptación y documentando desviaciones."
---

# Verificación Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Coordinación condicional: usa una instancia nueva de `gara-verifier` en modo `conformidad` para contrastar la implementación con contexto fresco. Entrega SPEC, PLAN, TAREAS, diff/código y consumidores, SHA observado y aceptación; devuelve evidencia por requisito, checks, hallazgos y límites sin editar. Para UI y con navegador real disponible, usa `gara-revisor-visual`: entrega URL, flujos/estados, temas y viewports, tokens, capacidades y archivos propios. Devuelve observaciones/capturas y solo corrige acabado dentro del ownership autorizado.

El coordinador escribe la sección `verification` del registro de `REVISION.md` definido en artifacts.md, con autor y sesión reales, y conserva por separado la revisión de corrección. Tras cambios de UI o código, repite la aceptación afectada para el SHA resultante. Comprueba el [contrato de delegación](references/delegation.md). Sin agentes, realiza la verificación y declara que faltó contexto independiente; sin navegador, registra los flujos no comprobados y limita el juicio visual a la evidencia disponible.

Comprueba qué está construido realmente; una tarea pendiente o bloqueada impide declarar completa la feature. El modo conformidad de gara-verifier revisa la correspondencia requisito, contrato, código y aceptación.

Ejecuta los criterios pertinentes y conserva SHA, comandos y salida real en REVISION.md. Para UI, recorre los flujos afectados con un navegador real cuando esté disponible y explica lo que no pudo comprobarse. No atribuyas resultados locales a CI remoto ni a producción.

Corrige desviaciones del alcance autorizado y valida las rutas afectadas. No edites SPEC, PLAN ni el contrato de aceptación para adaptar la promesa al resultado. Si el requisito exige una decisión nueva o cambiar arquitectura, registra el bloqueo y prepara una versión nueva.

Reconciliar contexto significa actualizar solo documentación y memoria afectadas, manteniendo commits de mediciones no repetidas. Usa gara-commit para las correcciones. Termina listo para revisión, sujeto al proceso humano de Gara; la revisión genérica de corrección corresponde a gara-review.

## Referencias

- [artifacts.md](references/artifacts.md)
- [runtime.md](references/runtime.md)
