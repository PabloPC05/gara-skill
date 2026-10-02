# Auditoría general de Gara Skill

Informe inicial: 30 de septiembre de 2026. Alcance: las 29 skills, los 10 roles, sus distribuciones Codex/Claude, el ejecutor, la instalación, la documentación y las pruebas. En esa fecha el directorio no tenía historial Git.

**Segunda auditoría (2 de octubre de 2026):** [skills y workflow](2026-10-02-skills-y-workflow.md), con el modelo de confianza de las aceptaciones y sus correcciones.

**Estado posterior:** los cambios y las regresiones están descritos en [corrections.md](corrections.md). Los apartados de dictamen y hallazgos siguientes conservan el diagnóstico inicial; [observations.json](observations.json) conserva sus resultados históricos. [resolution.json](resolution.json) registra la repetición de las siete reproducciones sobre la implementación corregida.

## Dictamen

La separación entre skills, agentes y coordinador es apropiada. Una skill pequeña puede ejecutarse directamente; delegar resulta útil cuando hay trabajo independiente, especialización o una revisión con contexto separado. Mantendría esta proporcionalidad.

La integración actual necesita una política de selección más explícita, contratos de delegación y comprobaciones de capacidades. Además, el ejecutor tiene defectos reproducibles que afectan a la validez del estado final. Las pruebas existentes pasan, pero no cubren estos casos. Priorizaría esas garantías antes de ampliar la automatización.

## Evidencia y límites

- Suite existente: **55 pruebas aprobadas en 208,580 segundos**. Ruff, formato y validación del catálogo aprobados.
- **Siete observaciones adicionales reproducidas** con repositorios temporales y el cliente simulado existente. No se utilizaron modelos reales ni servicios remotos en esas reproducciones.
- Los 316 archivos de la instalación actual coinciden con su manifiesto. Los 80 archivos útiles de `export/` coinciden byte a byte con el ZIP. `AGENTS.md` conserva su hash original.
- Las configuraciones nativas se contrastaron con documentación oficial. Esto verifica la semántica declarada; no demuestra el comportamiento de los diez agentes en tareas reales.
- El pase independiente de contexto está en [DOSSIER.md](../../audit-context/DOSSIER.md). Las observaciones están en [observations.json](observations.json).

Para repetir las comprobaciones adicionales desde la raíz:

```powershell
.venv/Scripts/python docs/audit/reproduce.py
```

El script utiliza exclusivamente fixtures y directorios temporales. Ahora exige que las siete reproducciones confirmen las correcciones y devuelve un código distinto de cero si alguna falla. Las regresiones adicionales viven en `tests/`; los datos históricos no se sobrescriben.

## Hallazgos por prioridad

P1: corregir antes de confiar en la automatización de entrega. P2: corregir para mejorar coherencia y fiabilidad. P3: aclaración o mejora de mantenimiento.

| ID | Prioridad | Hallazgo | Evidencia |
| --- | --- | --- | --- |
| A01 | P1 | La entrega puede modificar código validado y terminar como `completed` | Reproducción |
| A02 | P1 | La redacción conserva valores sensibles en JSON | Reproducción con datos ficticios |
| A03 | P2 | Las listas de herramientas Claude excluyen `Skill` y herramientas MCP | Configuración y documentación oficial |
| A04 | P2 | Una revisión vacía se acepta; no se registra quién revisó | Reproducción y lectura del ejecutor |
| A05 | P2 | La selección de agentes y los contratos de delegación son incompletos | Revisión de las 29 skills y 10 roles |
| A06 | P2 | El lock es por slug y permite varios coordinadores sobre un checkout | Reproducción del alcance del lock |
| A07 | P2 | El baseline UI exige una dependencia ausente y contradice la conservación del stack | Instrucciones y manifiesto Gara |
| A08 | P2 | Reinstalar conserva agentes retirados del catálogo | Reproducción en instalación temporal |
| A09 | P2 | La comprobación de rama confunde prefijos de issues | Reproducción |
| A10 | P3 | El dry-run de instalación no comprueba colisiones | Reproducción |

### A01 — La entrega puede invalidar la implementación verificada

En [runner.py](../../gara_workflow/runner.py), líneas 571–574 y 615–632, `publish` recibe el conjunto de todos los artefactos y archivos asignados. Después de esa fase se comprueba el texto de `ENTREGA.md`, pero no se vuelven a ejecutar las aceptaciones ni se compara la implementación con sus hashes verificados.

La reproducción modifica `feature.txt` de `done` a `broken` durante la entrega. El resultado sigue siendo `completed`, con `verify`, `review` y `publish` completos y cambios de código pendientes. No se publicó nada: el cliente y la URL de entrega son simulados.

**Corrección propuesta:** limitar las escrituras de entrega a sus artefactos, comprobar que la implementación validada se conserva y vincular la entrega al SHA observado. Una corrección de código debe volver a construcción/verificación. Añadir una regresión que rechace esta mutación, tanto si queda sin commit como si el cliente la registra.

### A02 — La redacción no cubre claves entrecomilladas

[common.py](../../gara_workflow/common.py), línea 52, oculta asignaciones simples y determinados tokens. Una entrada como `API_KEY=valor` se redacta; la misma información como un valor JSON de `api_key` o `token` permanece visible. [engines.py](../../gara_workflow/engines.py), líneas 113 y 237, guarda el resumen normalizado utilizando esa función.

La reproducción usa únicamente el valor ficticio `FAKE_AUDIT_SECRET_VALUE`: se elimina en una asignación simple, pero se conserva en JSON y en el log del resultado normalizado del adaptador. Descartar el stream bruto no cubre información sensible que aparezca en un resumen o error.

**Corrección propuesta:** redactar campos estructurados sensibles antes de serializar y cubrir representaciones entrecomilladas/escapadas en los textos. Probar el resultado persistido del adaptador, además de la función aislada, con valores ficticios. La redacción es una defensa adicional a la instrucción de no incluir secretos.

### A03 — Las capacidades Claude no coinciden con lo esperado

Las diez entradas `claude_tools` de [catalog.json](../../catalog.json), líneas 184–247, son listas cerradas de herramientas. Ninguna incluye `Skill` ni herramientas MCP. [packaging.py](../../gara_workflow/packaging.py), línea 191, las copia a cada agente.

En Claude, una lista `tools` limita las capacidades heredadas. Así, un agente puede leer un `SKILL.md` mediante `Read`, pero no invocarlo con `Skill`. `gara-revisor-visual` tampoco puede utilizar el navegador MCP del coordinador con esta configuración; una vía mediante CLI y `Bash` sigue siendo posible si existe. La documentación oficial distingue esos mecanismos. [Herramientas y skills de subagentes Claude](https://code.claude.com/docs/en/sub-agents).

**Corrección propuesta:** definir capacidades por necesidad y comprobarlas antes de delegar. Permitir `Skill` donde sea útil y el navegador ya autorizado para revisión visual, o documentar una alternativa CLI. Entregar rutas e instrucciones concretas en el briefing. Las fases explícitas no deben precargarse indiscriminadamente: Claude excluye de la precarga las skills con `disable-model-invocation: true`.

### A04 — El cierre de revisión no exige evidencia suficiente

[runner.py](../../gara_workflow/runner.py), líneas 603–613, exige que exista `REVISION.md`; no exige contenido ni un contrato mínimo. La reproducción deja ese archivo vacío en verificación y revisión y obtiene `completed`.

Además, las sesiones registran fase, ID, resumen y uso, pero no un inventario de subagentes utilizados. El ejecutor no puede acreditar por sí mismo que se utilizó `gara-verifier`, que el revisor fue independiente o que hubo revisión visual. Las aceptaciones ejecutadas sí aportan evidencia de los comandos declarados.

**Corrección propuesta:** comprobar un registro de revisión asociado al SHA, requisitos, aceptaciones, hallazgos y limitaciones. Conservar por separado las evidencias de verificación y revisión, aunque compartan archivo. Registrar roles/IDs de delegación mediante eventos sanitizados cuando el cliente los proporcione; en los demás casos declarar la información ausente. Una sesión nueva aporta contexto separado, pero no prueba una revisión humana. [Subagentes de Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents).

### A05 — La relación skill–agente no es uniforme

El recuento exacto es **3 agentes seleccionados por nombre, 4 mencionados mediante su función y 3 sin vínculo desde las skills**. `gara-review` solicita un revisor independiente sin fijar un perfil. La siguiente tabla diferencia el estado actual de una propuesta de selección:

| Agente | Conexión actual | Selección recomendada |
| --- | --- | --- |
| `gara-scout` | Ninguna | Exploración acotada en `gara-spec`/`gara-plan` cuando compense delegar |
| `gara-researcher` | Ninguna | Pregunta técnica externa concreta durante planificación |
| `gara-implementer` | Nombre explícito en `gara-build` | Mantener; briefing, archivos y aceptación completos |
| `gara-verifier` | Nombre explícito en `gara-verify` | Mantener; distinguir conformidad y revisión general |
| `gara-revisor-visual` | Ninguna | Comprobación de UI en `gara-verify`, con navegador disponible |
| `gara-investigador` | «Investigador» en el método de investigación | Síntesis de un ámbito cuando el dosier lo justifique |
| `gara-rastreador` | «Rastreadores» en `gara-investigar` | Recogida de fichas por ángulos independientes |
| `gara-contrastador` | «Contrastador» en `gara-investigar` | Contraste con informe y fuentes en contexto separado |
| `gara-evaluador` | Nombre explícito en las fases de `gara-convocatoria` | Mantener; rúbrica, pesos y elegibilidad |
| `gara-disenador` | «Diseñadores» en `gara-hero` | Variantes con dirección y archivos propios |

**Corrección propuesta:** documentar en cada skill si trabaja directamente o cuándo delega, el nombre exacto, entradas, archivos propios, salida y alternativa sin delegación. Elegir expresamente el perfil de `gara-review` y comprobar que su mandato cubre corrección/regresiones. Las skills pequeñas de PDF, logging, temas o accesibilidad pueden seguir ejecutándose directamente.

La ausencia de una llamada Python a cada agente es coherente con utilizar la delegación nativa de los clientes. El problema está en la ambigüedad de selección y evidencia, no en necesitar otro lanzador de procesos.

### A06 — El lock no excluye otra spec del mismo checkout

[runner.py](../../gara_workflow/runner.py), línea 543, toma el lock bajo el directorio de ejecución de cada slug. La reproducción adquiere simultáneamente locks para dos slugs del mismo checkout.

Esto confirma el alcance del lock; no simula una corrupción concurrente. Dos ejecuciones que compartan árbol, staging y rama pueden interferir antes de que las comprobaciones posteriores detecten cambios ajenos. El test actual utiliza la misma ruta de lock dos veces y no cubre distintos slugs.

**Corrección propuesta:** exclusión por checkout para los coordinadores que escriben, o exigir worktrees distintos. Mantener el estado por slug y añadir una prueba multiproceso del conflicto entre specs.

### A07 — El baseline UI conserva una obligación ajena al stack

[gara-baseline-ui](../../skills/gara-baseline-ui/SKILL.md), línea 30, obliga a usar `motion/react` cuando la animación requiere JavaScript. Su introducción prohíbe introducir dependencias incidentales. En el `frontend/package.json` de Gara inspeccionado no aparecen `motion` ni `framer-motion`; [gara-ui-animation](../../skills/gara-ui-animation/SKILL.md), línea 159, también contempla WAAPI.

Esto produce instrucciones incompatibles para una animación JavaScript que puede resolverse con la infraestructura existente. No se ejecutó una modificación real de UI para medir la decisión del modelo.

**Corrección propuesta:** adaptar las obligaciones a lo comprobado en Gara, preferir las APIs/dependencias existentes y reservar una librería nueva para una necesidad justificada. Revisar también las reglas absolutas de duración, primitivas y movimiento contra las skills especializadas. Conservar los recursos originales en `export/`.

### A08 — Los agentes retirados siguen instalados

[packaging.py](../../gara_workflow/packaging.py), línea 297, comienza el manifiesto nuevo con todos los archivos anteriores. La instalación actualiza el payload, pero no elimina archivos gestionados que desaparezcan del catálogo.

La reproducción instala un rol temporal, lo retira del catálogo y reinstala. El rol desaparece de la distribución compilada, pero permanece en `.claude/agents/`. Un cliente puede seguir descubriendo esa definición obsoleta.

**Corrección propuesta:** calcular archivos obsoletos del motor actualizado, borrarlos solo si siguen coincidiendo con el hash gestionado y preservar/bloquear modificaciones locales. No retirar archivos del otro motor durante una actualización parcial. Probar eliminación y renombrado de agentes, skills y helpers.

### A09 — El issue se compara como subcadena

[runner.py](../../gara_workflow/runner.py), línea 132, busca el texto del issue dentro del nombre de rama. Una SPEC de `GAR-12` supera el preflight en una rama correspondiente a `GAR-123`.

**Corrección propuesta:** comparar el identificador completo con límites apropiados y, cuando exista, la rama canónica indicada por Linear. Cubrir prefijos, ramas válidas y ramas sin issue. La reproducción es un dry-run sin llamadas al modelo.

### A10 — El dry-run de instalación ofrece una vista limitada

[packaging.py](../../gara_workflow/packaging.py), línea 239, devuelve antes de construir el payload y comprobar colisiones. La reproducción encuentra una previsualización `dry-run` satisfactoria seguida de un bloqueo por colisión en la instalación real. El archivo ajeno se conserva correctamente.

**Corrección propuesta:** reutilizar el mismo cálculo/preflight sin escritura para ambas modalidades, o documentar expresamente que el dry-run solo enumera destinos y componentes.

## Aspectos que conviene conservar

- Biblioteca estándar para el runtime y un único adaptador por protocolo nativo.
- Contratos de tareas con dependencias, cobertura, ownership y aceptación ejecutada por el coordinador.
- Hashes de SPEC/PLAN/contrato y recuperación antes de repetir una implementación interrumpida.
- Instalación con protección frente a archivos ajenos y ediciones locales.
- Publicación explícita, separación respecto a merge/despliegue y reconocimiento de la revisión humana.
- Roles especializados, sin asumir que un investigador pueda crear subagentes anidados.
- Recursos PDF locales, procedencia/licencias y conservación del paquete original.

## Mantenimiento y validación pendiente

`AGENTS.md` sigue describiendo un directorio sin código ni pruebas. Se conserva por la instrucción original del usuario; `README.md` y los manifests describen el estado actual. Esta discrepancia debe tenerse presente al orientar sesiones nuevas.

Las 55 pruebas usan clientes simulados. El registro previo acredita descubrimiento nativo, pero no completa una feature con los diez roles. Falta una prueba de comportamiento acotada por motor que observe selección, transmisión del briefing y evidencia devuelta, especialmente para revisión visual y skills especializadas. Windows es la plataforma comprobada; compatibilidad declarada con otras plataformas no equivale a una prueba realizada.

La política explícita de las fases está representada coherentemente en ambos clientes. Mantenerla implica que una petición genérica puede necesitar seleccionar la fase por nombre; conviene documentar esa decisión sin prometer activación automática. [Invocación de skills Codex](https://learn.chatgpt.com/docs/build-skills).

## Orden de corrección recomendado

1. Proteger la implementación durante entrega y ampliar la redacción de logs.
2. Exigir evidencia mínima de revisión y exclusión por checkout.
3. Explicitar la matriz de selección, los briefings y las capacidades por motor.
4. Corregir baseline UI, limpieza de instalaciones y comparación de issues.
5. Añadir regresiones y una evaluación de comportamiento aislada por cliente.

Esta auditoría añade informe, evidencia y reproducciones. No aplica todavía las correcciones propuestas al runtime, las skills, los roles ni la instalación del usuario.
