# Contrato de artefactos

Todos los archivos de una feature viven en `specs/<slug>/` del checkout de Gara. El slug usa minúsculas, números y guiones. Son Markdown legible por personas; no hay bloques JSON ni parsers: la comprobación es humana. `## Bloqueado` al inicio de línea en cualquier artefacto indica decisiones pendientes y detiene las fases que dependen de él. Esa sección lista cada bloqueo con qué falta, quién debe decidirlo y qué trabajo depende; se elimina solo cuando el usuario resuelve la decisión.

## SPEC.md

```yaml
---
issue: GAR-123
approved: false
---
```

`approved: true` registra una autorización real del usuario para esa versión concreta; no se infiere de silencio ni de una petición de análisis. Si el usuario ya autorizó implementar los requisitos presentados, conserva esa autorización sin pedirla de nuevo.

Cada requisito usa un encabezado `### R1 — Resultado observable` con escenarios normales, de fallo y criterios de aceptación. Registra alcance, exclusiones y decisiones materiales.

## PLAN.md

Módulos, contratos literales, errores, integración, restricciones y traducción de cada aceptación a un comando o prueba real. No contiene tareas ni estados. Se escribe justo antes de construir y queda estable; si cambian requisitos o arquitectura, prepara una versión nueva.

## TAREAS.md

Una sección por tarea, en el orden de ejecución, con esta plantilla:

````markdown
# Tareas — GAR-123

## Tanda 1

### T1 — Título corto
- Estado: pendiente        <!-- pendiente | en curso | bloqueada | verificada -->
- Requisitos: R1
- Depende de: —
- Archivos propios: `python/gara/domain/example.py`, `python/tests/domain/test_example.py`
- Punto de revisión: no    <!-- sí = parar tras la tanda para una comprobación humana concreta -->
- Briefing: contrato y comportamiento concreto, con entradas, salidas y casos límite.
- Aceptación:
  1. `cd python && python -m pytest tests/domain/test_example.py -q`
- Evidencia: _(la rellena gara-build con comando, código de salida y resumen real)_
````

- IDs únicos; cada requisito queda cubierto por alguna tarea y su aceptación.
- Una tarea nueva empieza en `pendiente`; si su aceptación falla, queda `en curso` con la evidencia del fallo, y pasa a `bloqueada` si depende de una decisión o permiso ajeno. Solo `gara-build` cambia estados, y solo tras ejecutar la aceptación y ver su resultado; el implementador no inventa resultados ni cambia pruebas para ponerlas en verde.
- Las dependencias están en tandas anteriores. Las tareas de una misma tanda no comparten archivos propios.
- Los contratos y pruebas que permiten dividir el trabajo van primero.
- La aceptación debe poder fallar: no uses `true`, `python -c pass` ni equivalentes. Usa rutas relativas con `/`, directorio de trabajo explícito y ninguna ruta de `.git`, `.claude/`, `.codex/`, `.husky/` ni `.env*`.
- El briefing basta para construir sin inventar decisiones materiales; la documentación adicional necesaria se cita de forma explícita. Si faltan datos, registra el hueco y bloquea lo dependiente.

## REVISION.md

Dos secciones independientes. `gara-verify` escribe *Verificación*; `gara-review` la conserva intacta y añade *Revisión*.

````markdown
# Revisión — GAR-123

## Verificación
- SHA verificado: `<SHA completo real>`
- Autor: nombre y rol reales (`gara-verifier`, sesión principal, persona…)
- Requisitos:
  - R1 — cumplido: escenario y archivo o salida observada
- Aceptaciones: T1.1 `comando` → código 0, resumen real
- Hallazgos: ninguno | lista con severidad (`low`, `medium`, `high`, `critical`), estado (`resuelto`, `aceptado`), resumen y evidencia
- Limitaciones: qué no se pudo comprobar (revisión humana pendiente, entorno…)

## Revisión
(mismos campos, sobre el SHA revisado)
````

El SHA identifica un commit existente, ancestro de HEAD, con los mismos archivos de implementación. Cada requisito y cada aceptación aparecen una vez. La autoría declarada no acredita independencia: si el verificador fue la misma sesión que implementó, o no hubo subagentes, dilo en *Limitaciones*. Un hallazgo sin resolver ni aceptar impide cerrar la revisión: regístralo como bloqueo. Si la revisión corrige código, indica el cambio y repite verify y review sobre el SHA nuevo.

## ENTREGA.md

Existe solo tras una orden explícita de publicar. Incluye URL de la PR, estado observado de Linear (`In Review`) y `Implementation SHA: <SHA de la revisión>`. Una vez escrito, el código, la SPEC, el PLAN, `TAREAS.md` y `REVISION.md` están cerrados: cualquier cambio posterior invalida la verificación y la revisión. La entrega acredita validación local; la aprobación humana y el despliegue son pasos aparte.
