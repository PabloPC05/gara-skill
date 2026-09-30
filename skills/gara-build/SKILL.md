---
name: "gara-build"
description: "Implementa tareas de TAREAS.md de Gara siguiendo los contratos y el horario autorizado, con validación concreta y progreso reanudable."
---

# Construcción Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Coordinación condicional: usa `gara-implementer` para tareas ya especificadas cuando separar la implementación aporte valor y la delegación esté disponible y autorizada. Entrega la tarea completa, contratos literales, checkout/HEAD, archivos propios, cambios que conservar y aceptación. Cada implementador escribe solo su ownership y devuelve cambios, salida real de los checks, rutas adicionales necesarias y bloqueos; el coordinador decide integración, estado y commit.

Comprueba el [contrato de delegación](references/delegation.md). El implementador no invoca gara-build, gara-workflow ni otro CLI de coordinación. Para una tarea pequeña o sin agentes, implementa en esta sesión siguiendo el orden y los mismos contratos.

Comprueba issue, asignación y rama conforme al proceso de Gara. Lee TAREAS.md y los archivos asignados; consulta solo las secciones del plan necesarias. Un briefing incompleto se registra como hueco, no se convierte silenciosamente en una decisión nueva.

Ejecuta las tandas programadas. Cuando elijas delegar, pasa cada tarea íntegra a gara-implementer. No lances otro CLI de coordinación dentro de la sesión. Si no hay agentes, ejecuta las tareas en orden y declara la limitación. Evita escritores simultáneos y suites paralelas que compartan recursos.

En ejecución guiada, ejecuta aceptación y conserva salida real antes de marcar verificado. En el ejecutor automático, este realiza la aceptación, escribe estados y solicita el commit después; no anticipes esos pasos ni cambies el contrato JSON. Los estados provisionales no son evidencia.

Conserva cambios previos, no amplíes el alcance y usa gara-commit para registros autorizados. Tras una interrupción, comprueba lo construido antes de repetir; un envío HPC incierto nunca se reenvía por deducción. Detén tareas dependientes si falta una decisión o permiso y continúa lo independiente cuando sea posible.

## Referencias

- [artifacts.md](references/artifacts.md)
- [runtime.md](references/runtime.md)
