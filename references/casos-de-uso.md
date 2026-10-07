# Casos de uso Gara

Qué skills invocar, en qué orden y qué agentes pueden intervenir. Los agentes nunca se lanzan solos: la skill te propone usarlos y solo lo hace con tu autorización ([delegación](delegation.md)). Sin agentes, la sesión principal hace el mismo trabajo y lo declara.

**Issue de Linear.** Todo trabajo que acabe en el código de Gara necesita un issue `GAR-N`, asignado a ti y en `In Progress`, y la rama que sugiere Linear. El issue va en el frontmatter de `SPEC.md` y su URL en la PR. Si la sesión no puede consultar Linear, la skill te pide que lo confirmes. Las tareas que no tocan el código (investigar, convocatorias, PDF, portadas) no lo necesitan.

## 1. Feature nueva

*Ejemplo: "exportar resultados de un cálculo a CSV desde el panel de resultados".* Necesita issue y rama.

| Paso | Skill | Agentes posibles | Qué haces tú al terminar |
| --- | --- | --- | --- |
| 1 | `/gara-grilling` (opcional) | — | Aclarar la idea si aún tiene dudas |
| 2 | `/gara-spec` | `gara-scout` para localizar código | Leer `SPEC.md` y poner `approved: true` |
| 3 | `/gara-plan` | `gara-scout`, `gara-researcher` si hay una duda técnica externa | Aceptar `PLAN.md` |
| 4 | `/gara-tasks` | — | Revisar tareas y comandos de aceptación |
| 5 | `/gara-build`, una vez por tanda | `gara-implementer` por tarea | Revisar el diff; `/gara-commit` si quieres registrar |
| 6 | `/gara-probar`, si el cambio se ve en la app (recomendado) | `gara-probador` en navegador real | Ver qué escenarios fallan; si falla alguno, otra `/gara-build` |
| 7 | `/gara-verify` | `gara-verifier` (conformidad); `gara-revisor-visual` y `gara-probador` si hay UI | Leer hallazgos |
| 8 | `/gara-review` | `gara-verifier` (corrección), instancia nueva | Decidir qué corregir o aceptar |
| 9 | `/gara-deliver` | — | Ordenar publicar; la revisión humana sigue pendiente |

Si la feature tiene pantalla nueva, aplica `/gara-frontend-design` durante el build o pide que la tarea lo indique en su briefing.

## 2. Bug pequeño y acotado

*Ejemplo: "el filtro de fechas excluye el último día".* Necesita issue y rama.

Puedes saltarte spec, plan y tareas: describe el fallo, pide la corrección con una prueba que lo reproduzca, revisa el diff y, si el fallo se veía en la app, comprueba el arreglo con `/gara-probar` recorriendo los pasos que lo reproducían; después `/gara-commit`. Si quieres una segunda mirada, `/gara-review` con `gara-verifier`. Si el arreglo crece (varios módulos, cambia un contrato o una migración), vuelve al caso 1.

## 3. Incidente con causa desconocida

*Ejemplo: "algunos trabajos HPC quedan en estado pendiente para siempre".* Necesita issue.

`/gara-spec` documenta síntomas y escenarios, separando lo observado de las hipótesis. `gara-scout` puede rastrear el código implicado. Cuando la causa esté clara, sigue el caso 1 o el 2 según su tamaño. Nunca se reenvía un trabajo HPC incierto para "probar".

## 4. Pantalla o flujo de interfaz

| Situación | Skill | Agente |
| --- | --- | --- |
| Pantalla, flujo o componente nuevo o rediseñado | `/gara-frontend-design` (dentro de una feature, caso 1) | `gara-revisor-visual` en verify |
| Comprobar que una feature funciona de punta a punta en la app | `/gara-probar` | `gara-probador` |
| Pulir una pantalla que ya existe | `/gara-baseline-ui` | — |
| Foco, teclado, contraste, lectores de pantalla | `/gara-fixing-accessibility` | — |
| Diseñar o ajustar una animación | `/gara-ui-animation` | — |
| Una animación va a trompicones | `/gara-fixing-motion-performance` | — |
| Cambio de vista que salta o pierde el foco | `/gara-view-transitions` | — |
| Tema claro/oscuro/sistema | `/gara-theme-switcher` | — |
| Teclado móvil que tapa un campo | `/gara-keyboard-avoidance` | — |
| Título, descripción o vista previa al compartir | `/gara-fixing-metadata` | — |
| Documentar el sistema visual | `/gara-diseno` | — |

Si el cambio modifica código de Gara, lleva issue. Antes de `/gara-commit`, recorre el resultado con `/gara-probar`: estas skills cambian lo que el usuario ve y hace.

## 5. Decisión o pregunta

| Situación | Skill | Agentes |
| --- | --- | --- |
| Poner a prueba un plan o una decisión propia | `/gara-grilling` | — |
| Pregunta científica, técnica o de negocio con fuentes | `/gara-investigar` | `gara-investigador`, `gara-rastreador`, `gara-contrastador` |
| Duda técnica concreta durante un plan | dentro de `/gara-plan` | `gara-researcher` |

## 6. Material fuera del código

| Situación | Skill | Agentes |
| --- | --- | --- |
| Analizar una convocatoria o redactar su memoria | `/gara-convocatoria` | `gara-evaluador` |
| Propuestas de portada para comparar | `/gara-hero` | `gara-disenador`, cada uno en su propio worktree |
| Generar un PDF con la marca Gara | `/gara-pdf` | — |

## 7. Retomar, cerrar y mejorar

- **Retomar** un trabajo a medias, o no saber por qué fase vas: `/gara-workflow`. Lee `specs/<slug>/` y Git y te dice la fase y los bloqueos.
- **Registrar** cambios en cualquier momento: `/gara-commit`, siempre bajo tu orden.
- **Aprender** de lo entregado: `/gara-retro` tras una entrega o cuando un fallo se repite.
- **Buscar** una skill que no está aquí: `/gara-find-skills`.
