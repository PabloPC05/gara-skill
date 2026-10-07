---
name: "gara-spec"
description: "Define y documenta requisitos de una feature o incidente de Gara mediante una entrevista basada en hechos; usar al inicio de un trabajo nuevo, antes de decidir la implementación, o cuando el usuario pida escribir o revisar SPEC.md."
disable-model-invocation: true
---

# Especificación Gara

Lee el [perfil Gara](references/gara.md), el [flujo manual](references/flujo.md) y aplica las instrucciones del checkout objetivo. Solo escribe `specs/<slug>/SPEC.md`.

## Pasos

1. Explora el checkout y las evidencias antes de preguntar. Si hay preguntas de código acotadas cuya exploración compense separar, delega en `gara-scout` según el [contrato de delegación](references/delegation.md); sin agentes, explora tú y deja lo no localizado como incertidumbre.
2. Entrevista sobre resultados de producto, fallos, recuperación y exclusiones; las decisiones técnicas son de `gara-plan`. Agrupa de una a tres decisiones independientes por ronda, con opciones y consecuencias. Resuelve los hechos con herramientas; para detalles reversibles dentro del alcance, decide con criterio.
3. Escribe una SPEC autocontenida según el [contrato de artefactos](references/artifacts.md): issue real, requisitos `R1…`, escenarios y alcance. Distingue observaciones de hipótesis y no infieras una causa remota de un síntoma. Para interfaz, parte del sistema visual vigente y pregunta solo decisiones nuevas.
4. Deja `approved: false`. Solo pasa a `true` si el usuario autoriza esta versión de forma explícita (incluida una autorización ya dada en la conversación). Registra las decisiones materiales pendientes con `## Bloqueado`.

Para cambios pequeños, usa una SPEC proporcional; no impongas una entrevista extensa.

## Parada

Termina aquí; no planifiques ni pases de fase. Devuelve: resumen de la SPEC, archivo escrito, decisiones pendientes (`## Bloqueado`, estado de `approved`) y siguiente fase sugerida: `/gara-plan` cuando el usuario apruebe.

## Referencias

- [artifacts.md](references/artifacts.md)
- [delegation.md](references/delegation.md)
- [flujo.md](references/flujo.md)
