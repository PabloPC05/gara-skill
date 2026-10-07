---
name: "gara-review"
description: "Revisa el diff de Gara en busca de fallos de corrección, regresiones y pruebas ausentes, con independencia del plan, y escribe la sección Revisión de REVISION.md; usar tras gara-verify."
disable-model-invocation: true
---

# Revisión de corrección Gara

Lee el [perfil Gara](references/gara.md), el [flujo manual](references/flujo.md) y aplica las instrucciones del checkout objetivo. Solo añade la sección `## Revisión` a `specs/<slug>/REVISION.md` y conserva intacta `## Verificación` (plantilla en el [contrato de artefactos](references/artifacts.md)). No edites código ni SPEC/PLAN.

## Pasos

1. Parte del diff y sus consumidores con contexto fresco. Si compensa, delega en una instancia nueva de `gara-verifier` en modo `correccion`, distinta de quien implementó, según el [contrato de delegación](references/delegation.md); sin agentes, revisa tú y declara en *Limitaciones* que no hay independencia (un autoinforme no la acredita).
2. Busca errores de comportamiento, contratos rotos, autorización, estados concurrentes y casos límite. Investiga cada candidato y reprodúcelo cuando sea posible; una sospecha no es un fallo confirmado. Estilo, refactors y rendimiento sin medir son opcionales y no bloquean.
3. Registra cada hallazgo con severidad, ubicación, desencadenante y evidencia, y estado `resuelto` o `aceptado`. Uno sin resolver ni aceptar impide cerrar la revisión: regístralo como `## Bloqueado`.
4. No corrijas por tu cuenta. Si el usuario pide una corrección, aplícala dentro del alcance y ejecuta la aceptación afectada; verify y review deben repetirse sobre el SHA nuevo. Cambios de requisito o migraciones nuevas vuelven a `/gara-plan`.

## Parada

Termina aquí; no publiques ni marques `Done`. Devuelve: resumen, archivo tocado, hallazgos por severidad y limitaciones, decisiones pendientes (qué corregir o aceptar) y siguiente fase sugerida: `/gara-deliver` si la revisión está cerrada, o `/gara-build` y repetir verify y review si hay correcciones.

## Referencias

- [artifacts.md](references/artifacts.md)
- [delegation.md](references/delegation.md)
- [flujo.md](references/flujo.md)
