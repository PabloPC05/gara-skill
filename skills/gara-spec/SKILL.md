---
name: "gara-spec"
description: "Define y documenta requisitos de una feature o incidente de Gara mediante una entrevista basada en hechos; usar antes de decidir la implementación."
---

# Especificación Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Coordinación condicional: usa `gara-scout` cuando hay preguntas de código acotadas cuya exploración conviene separar. Entrega preguntas completas, checkout/HEAD, evidencias iniciales y rutas de interés; el scout solo lee y devuelve rutas, símbolos, hechos y límites. El coordinador entrevista y escribe `SPEC.md`.

Comprueba el [contrato de delegación](references/delegation.md) antes del encargo. Sin agentes, realiza la exploración en esta sesión y conserva el mismo alcance; una búsqueda incompleta queda como incertidumbre.

Explora el checkout y las evidencias antes de preguntar. Entrevista sobre resultados de producto, fallos, recuperación y exclusiones; las decisiones técnicas corresponden a gara-plan. Agrupa de una a tres decisiones independientes por ronda, con opciones y consecuencias. Resuelve hechos mediante herramientas y usa criterio para detalles reversibles dentro del alcance.

Escribe una SPEC autocontenida en `specs/<slug>/SPEC.md`, con issue real, requisitos R1, R2 y escenarios de aceptación. Distingue observaciones de hipótesis y no infieras una causa remota de un síntoma. Para interfaz, usa el sistema visual vigente; si no existe documentación suficiente, deriva lo comprobable del código y pregunta únicamente decisiones nuevas.

Registra las decisiones materiales pendientes como bloqueos. `approved: true` solo refleja una autorización real para esa versión, incluida una autorización ya dada en la conversación. La ausencia de respuesta no aprueba. Una petición de investigar o planificar conserva ese alcance.

Para cambios pequeños, usa una especificación proporcional; no impongas una entrevista extensa. Consulta el contrato de artefactos antes de preparar una ejecución automática.

## Referencias

- [artifacts.md](references/artifacts.md)
- [runtime.md](references/runtime.md)
