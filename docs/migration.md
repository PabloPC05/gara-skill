# Catálogo y adaptación

`catalog.json` relaciona todos los componentes del ZIP original con su destino. Son **29 skills y 10 roles**, generados para cada motor. El ejecutor tiene una única implementación común; no hay dos drivers divergentes.

## Skills y comandos

| Original | Gara |
| --- | --- |
| spec, plan, tasks, build, verify | gara-spec, gara-plan, gara-tasks, gara-build, gara-verify |
| osix-build | gara-workflow |
| diseno, workflow-setup, workflow-health, retro | Prefijo `gara-`, contexto y evidencia de Gara |
| investigar, convocatoria, grilling | Prefijo `gara-`, fuentes trazables y criterios científicos reales |
| osix-pdf | gara-pdf: Lato y logo Gara, recursos locales, sin datos fiscales ficticios |
| frontend-design, baseline-ui | Prefijo `gara-`, sistema visual existente |
| ui-animation, fixing-accessibility, fixing-motion-performance, fixing-metadata | Prefijo `gara-`, referencias y helpers reutilizables conservados |
| hero | gara-hero: opciones de presentación del producto, sin promoción científica inventada |
| android-theme-switcher + rn-theme-switcher | gara-theme-switcher: temas web claro/oscuro/sistema vigentes |
| rn-keyboard-avoidance | gara-keyboard-avoidance: viewport y formularios web |
| rn-stack-transitions | gara-view-transitions: paneles, pestañas y diálogos web |
| logger-system, find-skills | gara-logger-system, gara-find-skills |
| osix-commit | gara-commit existente, validador portable para Claude |
| Nuevas | gara-review y gara-deliver separan revisión y entrega explícita |

Se mantienen las fases originalmente explícitas sin fijar el modelo. Los comandos se convierten en skills para funcionar en ambos motores. No se instalan nombres OSIX o RN que puedan activar instrucciones del proyecto anterior.

## Agentes

Los diez roles se conservan con prefijo `gara-`: scout, implementer, verifier, revisor-visual, researcher, investigador, rastreador, contrastador, evaluador y disenador. Se generan TOML nativos para Codex y Markdown con frontmatter para Claude. Heredan el modelo. Los roles de exploración y contraste no editan el checkout; las ejecuciones que necesiten escritura corresponden al coordinador.

La coordinación limita tandas a tres tareas y carga cuatro, con dependencias anteriores y archivos sin colisión dentro de la tanda. Una aceptación independiente comprueba lo implementado. No se presupone delegación anidada: investigador solicita al coordinador los rastreadores.

## Scripts

| Original | Subcomando actual |
| --- | --- |
| osix-build | run |
| osix-reanudar | resume |
| osix-metricas | metrics |
| osix-fixes | fixes |
| claude-sesiones | sessions |
| vigilar-agenda | watch |
| osix-build-2, osix-forge | Conservados como históricos en export; no instalados |

`sessions` observa solo sesiones del ejecutor Gara, sin enumerar ni matar sesiones ajenas. `fixes` recoge commits de corrección sin inventar categorías. `watch` observa JSON local o un archivo remoto indicado explícitamente por SSH; no inicia trabajos ni lleva un servidor personal preconfigurado.

La recuperación se basa en estado, hashes y aceptación real, sin ventanas de cuota fijas ni bypass de permisos. Los trabajos científicos inciertos no se reenvían. Los estándares actuales de `.ai/`, Linear y el CI del checkout prevalecen sobre las fotografías históricas.
