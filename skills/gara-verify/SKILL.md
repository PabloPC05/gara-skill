---
name: "gara-verify"
description: "Verifica una implementación construida de Gara contra SPEC, PLAN y TAREAS, ejecutando la aceptación y escribiendo la sección Verificación de REVISION.md; usar tras gara-build, antes de la revisión de corrección."
disable-model-invocation: true
---

# Verificación Gara

Lee el [perfil Gara](references/gara.md), el [flujo manual](references/flujo.md) y aplica las instrucciones del checkout objetivo. Solo escribe la sección `## Verificación` de `specs/<slug>/REVISION.md` (plantilla en el [contrato de artefactos](references/artifacts.md)); no edites código, SPEC, PLAN ni aceptaciones.

## Pasos

1. Comprueba qué está construido: una tarea `pendiente`, `en curso` o `bloqueada` impide declarar completa la feature; regístralo. Fija el SHA verificado, que debe ser un commit existente; si hay cambios sin commitear, indícalo en *Limitaciones* en vez de atribuirlos a un SHA.
2. Contrasta requisito por requisito (SPEC, contratos del PLAN, código y aceptación) y ejecuta tú las aceptaciones pertinentes. Si compensa, delega en una instancia nueva de `gara-verifier` en modo `conformidad`; para UI con navegador real disponible, en `gara-revisor-visual`. Ambos según el [contrato de delegación](references/delegation.md): sin agentes o sin navegador, hazlo tú y declara en *Limitaciones* la falta de contexto independiente o los flujos no comprobados.
3. Escribe la sección con autor y rol reales, requisitos, aceptaciones con su salida, hallazgos y limitaciones. No atribuyas resultados locales a CI remoto ni a producción.
4. Las desviaciones se registran como hallazgos; corregirlas es decisión del usuario (otra `/gara-build` o un cambio acotado que él pida). Si el requisito exige una decisión nueva, registra `## Bloqueado`.

## Parada

Termina aquí; no corrijas ni lances la revisión. Devuelve: resumen, archivo tocado, hallazgos y limitaciones, decisiones pendientes y siguiente fase sugerida: `/gara-review` si no hay desviaciones, o `/gara-build` para corregirlas.

## Referencias

- [artifacts.md](references/artifacts.md)
- [delegation.md](references/delegation.md)
- [flujo.md](references/flujo.md)
