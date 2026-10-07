---
name: "gara-convocatoria"
description: "Usar cuando el usuario pida analizar una convocatoria de financiación o ayuda para Gara, evaluar candidatas o redactar una memoria contra sus bases y rúbrica. Prepara documentos; no presenta ni envía solicitudes. Para investigación general usa gara-investigar."
disable-model-invocation: true
---

# Convocatorias Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo. Sigue el [contrato de fases y entregables](references/phases.md); si vas a delegar, el [contrato de delegación](references/delegation.md).

## Ejecución

Coordinada y condicional: con autorización del usuario, `gara-evaluador` puede puntuar candidatas o la memoria en contexto fresco cuando compense separar la evaluación. Recibe bases oficiales con versión/fecha, elegibilidad, rúbrica con pesos, IDEAS o MEMORIA y evidencias de capacidades reales, sin una clasificación esperada. Sin agentes, evalúa tú contra la misma rúbrica y declara que faltó contexto independiente.

El coordinador lee personalmente las bases completas, escribe `EVALUACION.md` y prepara la memoria. El evaluador no edita ni coordina investigadores.

## Reglas

- Los datos de elegibilidad, cofinanciación, personalidad jurídica, socios, fiscalidad y resultados salen de las bases o de evidencia aportada; si falta uno decisivo, registra el bloqueo y pregunta. No inventes nada de eso.
- Un incumplimiento duro descarta la candidata; no se disimula como nota baja.
- La investigación de contexto usa el método de `gara-investigar` (fuentes primarias y fichas) aplicado directamente, o ya lanzado por el usuario.
- Si piden PDF, el usuario lo genera después con `gara-pdf`, salvo que la convocatoria obligue a otra plantilla.
- Presentar la solicitud, firmar, contactar con el organismo o comprometer a terceros solo se hace si el usuario lo ordena expresamente.

## Parada

Una fase por invocación. Reanuda desde los archivos existentes sin repetir fases ni sustituir las bases por resúmenes. Al terminar la fase devuelve artefacto, bloqueos, decisiones pendientes y fase siguiente posible, y espera al usuario.
