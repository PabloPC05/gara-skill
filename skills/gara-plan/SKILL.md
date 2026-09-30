---
name: "gara-plan"
description: "Diseña la arquitectura y validación de una SPEC autorizada de Gara; usar antes de dividir el trabajo en tareas."
---

# Plan técnico Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Coordinación condicional: usa `gara-scout` para localizar módulos y consumidores cuando compense separar esa exploración, y `gara-researcher` para una pregunta técnica externa concreta que requiera fuentes primarias. Entrega al scout SPEC, checkout/HEAD, preguntas y rutas; devuelve ubicaciones y evidencia sin editar. Entrega al researcher la pregunta, versiones, restricciones y fuentes iniciales; devuelve respuesta, URLs, fechas y límites sin cambiar código.

El coordinador integra las respuestas y escribe únicamente `PLAN.md`. Comprueba el [contrato de delegación](references/delegation.md). Sin agentes, explora y consulta documentación directamente; si falta acceso a una fuente necesaria, registra el supuesto pendiente.

Lee la SPEC y el código actual: módulos afectados, tipos, consumidores, tests y configuración. Comprueba supuestos contra HEAD; un diseño basado en un baseline histórico no describe automáticamente el checkout.

Escribe exclusivamente PLAN.md: contratos literales, estados y errores, restricciones, fuera de alcance, integración y traducción de cada aceptación a una prueba o comando real. Resuelve preguntas técnicas mediante exploración o documentación primaria; una decisión material de producto vuelve al usuario.

No implementes ni dividas en tareas. Los cambios de esquema incluyen modelo y migración Alembic; los plugins respetan su SDK público. Para frontend, identifica flujos y estados que requieren comprobación visual contra los tokens existentes.

Planifica justo antes de construir. El plan queda estable durante ejecución y verificación; un cambio sustancial abre una versión nueva. Ante un supuesto falso o una autorización ausente, escribe `## Bloqueado`. Respeta el modo de conversación y sus posibilidades reales de escritura.

## Referencias

- [artifacts.md](references/artifacts.md)
- [runtime.md](references/runtime.md)
