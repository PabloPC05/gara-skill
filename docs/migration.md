# Adaptación y cambios

## Origen

Las skills y roles proceden de un `export.zip` de OSIX (Android/React Native), adaptadas a Gara (React/Vite/TypeScript, FastAPI): prefijo `gara-`, sistema visual y pruebas del checkout y fuentes trazables. `export/` y `export.zip` son locales y no forman parte del repositorio.

| Original | Gara |
| --- | --- |
| spec, plan, tasks, build, verify | gara-spec, gara-plan, gara-tasks, gara-build, gara-verify |
| osix-build | gara-workflow (guía manual del orden de fases) |
| diseno, retro | gara-diseno, gara-retro |
| investigar, convocatoria, grilling | Prefijo `gara-`, fuentes trazables y criterios científicos reales |
| osix-pdf | gara-pdf: Lato y logo Gara, recursos locales |
| frontend-design, baseline-ui, ui-animation, fixing-* | Prefijo `gara-`, referencias y helpers conservados |
| hero | gara-hero |
| android-theme-switcher + rn-theme-switcher | gara-theme-switcher |
| rn-keyboard-avoidance | gara-keyboard-avoidance |
| rn-stack-transitions | gara-view-transitions |
| logger-system, find-skills | gara-logger-system, gara-find-skills |
| osix-commit | gara-commit |
| Nuevas | gara-review y gara-deliver |

Los diez agentes se conservan con prefijo `gara-`: scout, implementer, verifier, revisor-visual, researcher, investigador, rastreador, contrastador, evaluador y disenador.

## Paso a control manual (octubre de 2026)

Se eliminó el ejecutor Python (`gara_workflow/`), su CLI, el instalador, el catálogo `catalog.json`, la suite de pruebas del ejecutor y las skills `gara-workflow-setup` y `gara-workflow-health`, que solo existían para operarlo. Quedan 27 skills y 10 agentes, y la distribución para Codex (`openai.yaml`, agentes `.toml`) dejó de generarse: el repositorio es ahora la fuente nativa de Claude Code.

Consecuencias:

- Las fases ya no se encadenan ni guardan estado privado: cada una la invoca el usuario y se detiene.
- `TAREAS.md` y `REVISION.md` son Markdown legible, sin bloques JSON ni hashes validados por script. Las aceptaciones las ejecuta `gara-build` en la sesión del usuario, que las revisa antes de construir.
- La validación del bundle es `scripts/check.sh`; se pierden las comprobaciones de integridad del instalador (manifiesto de hashes, evidencia ligada al SHA verificada por código).
- `docs/audit/` conserva el diagnóstico de la versión con ejecutor; sus scripts de reproducción y la validación asociada ya no existen. Consúltalos en el historial de Git anterior a este cambio.
