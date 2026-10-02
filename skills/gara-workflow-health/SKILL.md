---
name: "gara-workflow-health"
description: "Audita la salud del flujo Gara usando sus estados, tareas y resúmenes de sesiones reales; usar para diagnosticar fallos de proceso."
---

# Salud del flujo Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe checkout, slug y artefactos del periodo; entrega métricas, evidencia, huecos y límites de proceso. Si faltan sesiones o estados, declara datos ausentes y analiza lo disponible. No requiere delegación.

Usa scripts/health.py con el checkout y slug para medir cobertura de requisitos, estados, gates registrados y sesiones normalizadas. Revisa una muestra de briefings y PLAN contra código; una aceptación vacía o una marca verified no demuestran calidad. Distingue contadores observados de conclusiones inferidas y datos ausentes de cero. Informa huecos, tiempos y límites sin proyectar métricas históricas sobre otro HEAD. No alteres automáticamente el proceso ni clasifiques como fallo una espera legítima en In Review.

## Referencias

- [artifacts.md](references/artifacts.md)
- [runtime.md](references/runtime.md)
