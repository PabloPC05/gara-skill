# Ejecución y delegación Gara

`direct` ejecuta la skill en la sesión actual. `coordinated` permite delegar bajo las condiciones indicadas; no obliga a lanzar agentes. El *coordinador* es la sesión principal que dirige el usuario: selecciona y lanza los agentes. **Delegar necesita autorización del usuario**: si la skill no la trae ya (porque el usuario pidió explícitamente usar agentes), propón qué agente lanzarías y para qué antes de hacerlo. Los agentes `gara-*` no tienen `disable-model-invocation`, así que Claude podría ofrecerlos por su descripción; no los uses sin esa autorización. Las skills pequeñas conservan ejecución directa.

## Comprobar capacidades

Antes de delegar, comprueba autorización vigente, disponibilidad del agente exacto, lectura de las rutas del briefing, escritura dentro de su ownership y herramientas necesarias. Para investigación comprueba acceso a las fuentes; para revisión visual, un navegador real y la URL del entorno autorizado. Que un agente exista en `agents/` no acredita estas capacidades. Adapta las tandas a los límites del cliente y evita escritores o suites que compartan recursos.

En el frontmatter de cada agente, `tools` limita herramientas. `Skill` permite usar una skill especializada disponible; su ausencia exige pasar las instrucciones pertinentes en el briefing. Sin `tools` se conserva el conjunto heredado; es el caso de `gara-revisor-visual`, para no excluir el navegador MCP ya disponible y autorizado. `disallowedTools: Agent` impide delegación anidada. Estas declaraciones no conceden permisos, habilitan servidores MCP ni garantizan herramientas que el cliente no ofrece. Los modelos y permisos siguen heredados.

No precargues fases con `disable-model-invocation: true` ni cambies su política explícita. El coordinador transmite el contrato de la fase ya seleccionada y las rutas o instrucciones especializadas necesarias. Un trabajador no invoca la fase que lo lanzó ni `gara-workflow`, y las fases no se invocan entre sí; `gara-implementer` no invoca `gara-build`. No lances otro CLI para suplir la delegación.

Si falta delegación, ejecuta el mismo alcance secuencialmente y declara la limitación. Si falta una capacidad necesaria para la aceptación, registra qué no se comprobó; una revisión de código o una captura previa no sustituye navegación o ejecución real. No amplíes permisos ni configuración global para resolverlo.

## Briefing y devolución

Cada encargo incluye agente y modo, objetivo acotado, checkout y SHA o baseline observado, requisitos/contratos literales, preguntas o flujos, rutas de entrada, archivos o prefijos propios, capacidades comprobadas, aceptación y salida esperada. Entrega las instrucciones del checkout que el trabajador necesita; no asumas que hereda la conversación o las skills del coordinador. Informa de otros escritores y de los cambios que debe conservar.

Un trabajador devuelve rutas o ubicaciones, hallazgos y evidencia, comandos ejecutados con resultado real, cambios propios si los tiene, dudas y límites. No cambia requisitos, contratos de aceptación, estados finales ni decisiones de publicación. El coordinador revisa la devolución, integra artefactos y registra agente/modo e ID de sesión si está disponible; si no, declara ese dato ausente. Evita secretos en briefings y registros.

`gara-verifier` utiliza una instancia nueva sin participación en la implementación: modo `conformidad` en verify y modo `correccion` en review. Recibe artefactos y código bruto, sin las conclusiones esperadas ni el historial de razonamiento del implementador; no reutilices su sesión o un fork de ese contexto. Devuelve evidencia al coordinador, que conserva separados ambos modos en `REVISION.md` para el SHA comprobado. Si una corrección modifica código, repite la aceptación afectada y la revisión pertinente sobre el nuevo SHA. Una ejecución directa declara que faltó contexto independiente. Ningún agente sustituye la aprobación humana.

## Matriz de selección

| Skill | Ejecución | Agente y condición |
| --- | --- | --- |
| `gara-spec` | coordinated | `gara-scout`: preguntas de código acotadas que compensen separar la exploración |
| `gara-plan` | coordinated | `gara-scout`: rutas/consumidores; `gara-researcher`: pregunta técnica externa concreta |
| `gara-tasks` | direct | Sin agentes; prepara contratos y briefings |
| `gara-build` | coordinated | `gara-implementer`: tareas completas con ownership y aceptación |
| `gara-verify` | coordinated | `gara-verifier` en `conformidad`; `gara-revisor-visual` para acabado de UI y `gara-probador` para recorrer los flujos, con navegador disponible |
| `gara-probar` | coordinated | `gara-probador`: escenarios de la SPEC en navegador real (browser-harness local) |
| `gara-review` | coordinated | `gara-verifier` en `correccion`, con contexto fresco |
| `gara-workflow` | direct | Sin agentes; guía manual del orden de fases y puntos de control |
| `gara-deliver` | direct | Sin agentes; entrega autorizada mediante capacidades autenticadas |
| `gara-diseno` | direct | Sin agentes; documenta el sistema visual observado |
| `gara-retro` | direct | Sin agentes; propone mejoras sustentadas |
| `gara-investigar` | coordinated | `gara-investigador`: síntesis de ámbito; `gara-rastreador`: fuentes por ángulo; `gara-contrastador`: informe y fichas en contexto fresco |
| `gara-convocatoria` | coordinated | `gara-evaluador`: candidatas o memoria contra bases, elegibilidad y rúbrica |
| `gara-grilling` | direct | Sin agentes; entrevista y decisiones pendientes |
| `gara-pdf` | direct | Sin agentes; PDF renderizado y comprobado |
| `gara-frontend-design` | direct | Sin agentes; diseño/cambios del alcance y comprobación de UI |
| `gara-hero` | coordinated | `gara-disenador`: variantes independientes con dirección y archivos propios |
| `gara-theme-switcher` | direct | Sin agentes; temas, persistencia y pruebas pertinentes |
| `gara-keyboard-avoidance` | direct | Sin agentes; formularios y comprobación de viewport/teclado |
| `gara-view-transitions` | direct | Sin agentes; transiciones y comprobación de estado/foco |
| `gara-logger-system` | direct | Sin agentes; logging y evidencia de redacción/niveles |
| `gara-find-skills` | direct | Sin agentes; selección e integración autorizada de capacidades |
| `gara-baseline-ui` | direct | Sin agentes; hallazgos o correcciones de acabado |
| `gara-fixing-accessibility` | direct | Sin agentes; hallazgos o correcciones accesibles |
| `gara-fixing-motion-performance` | direct | Sin agentes; diagnóstico medido y correcciones |
| `gara-fixing-metadata` | direct | Sin agentes; metadatos y validación del alcance publicado |
| `gara-ui-animation` | direct | Sin agentes; movimiento o medición y validación |
| `gara-commit` | direct | Sin agentes; staging validado y commit autorizado |

Esta matriz identifica los agentes seleccionables por cada skill; la coordinación sigue siendo condicional. Cuando una fase necesita otra skill explícita, conserva su autorización y selección vigente. En particular, la investigación de una convocatoria aplica el método de `gara-investigar` ya seleccionado o lo realiza directamente; el evaluador no coordina investigadores.

La semántica de herramientas y skills está documentada en [subagentes Claude](https://code.claude.com/docs/en/sub-agents) y [skills Claude](https://code.claude.com/docs/en/skills).
