---
name: "gara-workflow-setup"
description: "Prepara un checkout Gara para el flujo documentado: detecta comandos, verifica configuración y propone integración con las instrucciones existentes."
---

# Preparación del flujo Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe checkout y preparación autorizada; entrega comandos comprobados, índice/configuración del alcance y capacidades o pendientes. Si falta una herramienta, documenta el requisito sin inventar una integración. No requiere delegación.

Lee los manifests, lockfiles, CI y reglas del checkout. Detecta comandos disponibles y configura un índice de specs y artefactos versionados cuando se haya autorizado la preparación. Usa doctor para capacidades. Conserva AGENTS.md, CLAUDE.md y la memoria canónica; propone mejoras concretas si son necesarias, sin reemplazarlos. No copies hooks de Claude a Codex ni ejecutes suites completas tras cada edición. Una integración con hooks requiere una necesidad concreta y el formato y confianza del motor real. No cambies dependencias, thresholds o workers incidentalmente.

## Referencias

- [runtime.md](references/runtime.md)
- [artifacts.md](references/artifacts.md)
