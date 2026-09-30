# Contrato de artefactos v1

Todos los archivos de una feature viven en `specs/<slug>/`. El slug usa minúsculas, números y guiones. El índice humano de specs puede enlazarlos; Linear conserva su propio estado.

## SPEC.md

Frontmatter mínimo:

```yaml
---
issue: GAR-123
approved: true
---
```

`approved: true` registra una autorización real del usuario para esa versión concreta; no se infiere de silencio, timeout o de una petición de análisis. Si ya autorizó implementar los requisitos presentados, conserva esa autorización sin volver a pedirla.

Cada requisito utiliza un encabezado `### R1 — Resultado observable`. Incluye escenarios normales, fallos y criterios de aceptación. Registra alcance, exclusiones y decisiones materiales. `## Bloqueado` indica que faltan decisiones y detiene el flujo automático.

## PLAN.md

Describe módulos, contratos literales, errores, integración, restricciones y traducción de aceptación a comandos. No contiene tareas ni estados. Se escribe justo antes de construir y queda estable durante la ejecución. Si cambian requisitos o arquitectura, prepara una versión nueva y un flujo nuevo; no reescribas el diseño histórico para ocultar lo ocurrido.

## TAREAS.md

Es Markdown legible con un bloque JSON identificado por `<!-- gara-tasks:v1 -->`. El bloque es la fuente de verdad sobre tareas y horario; evita tablas paralelas con estados contradictorios.

<!-- example only -->
````markdown
# Tareas

<!-- gara-tasks:v1 -->
```json
{
  "version": 1,
  "issue": "GAR-123",
  "tasks": [
    {
      "id": "T1",
      "requirements": ["R1"],
      "depends_on": [],
      "files": ["python/gara/domain/example.py", "python/tests/domain/test_example.py"],
      "briefing": "Contrato y comportamiento concreto, con entradas, salidas y casos límite.",
      "acceptance": [
        {"cwd": "python", "argv": ["python", "-m", "pytest", "tests/domain/test_example.py", "-q"], "timeout": 600}
      ],
      "status": "pending",
      "weight": 1,
      "checkpoint": false
    }
  ],
  "batches": [["T1"]]
}
```
````

Los nombres del ejemplo ilustran el formato: el plan debe identificar rutas y pruebas reales del checkout. `argv` es una lista de argumentos, no una cadena de shell. Usa rutas relativas con `/`; no asignes directorios, glob patterns, rutas absolutas o `.git`.

- IDs únicos; cada requisito debe estar cubierto por alguna tarea y su aceptación.
- Dependencias programadas en tandas anteriores; no hay dependencia dentro de una tanda.
- Hasta tres tareas por tanda, sin colisiones de archivos; carga total máxima 4. Pesos: 1 ligera, 2 pesada, 4 exclusiva. Si una aceptación arranca la aplicación o usa recursos compartidos, programa esa tarea de manera conservadora.
- Los contratos y pruebas que permiten dividir el trabajo van primero. Prioriza el riesgo entre tareas con las mismas dependencias.
- Estados: `pending`, `running`, `blocked`, `verified`. El ejecutor escribe estados y `evidence` después de ejecutar la aceptación. El implementador no inventa resultados ni cambia pruebas para declararlas verdes.
- `checkpoint: true` pausa después de la tanda para una comprobación humana; `resume --ack-checkpoint` registra que se revisó.

El briefing debe bastar para construir sin inventar decisiones materiales. La lectura de documentación adicional necesaria es explícita. Si faltan datos, registra el hueco y bloquea lo dependiente.

## REVISION.md

Contiene un único bloque `<!-- gara-review:v1 -->` seguido de JSON. `verify` escribe `verification`; `review` conserva ese registro exactamente y añade `review` con los mismos campos. Ejemplo de verificación:

````markdown
<!-- gara-review:v1 -->
```json
{
  "version": 1,
  "issue": "GAR-123",
  "verification": {
    "implementation_sha": "<SHA completo real de la implementación>",
    "author": {"name": "Autor real", "role": "gara-verifier"},
    "requirements": [
      {"id": "R1", "result": "passed", "evidence": "Escenario y archivo o salida observada"}
    ],
    "checks": [
      {"task": "T1", "gate": 1, "returncode": 0, "summary": "Comando y resultado real"}
    ],
    "findings": [],
    "limitations": ["Revisión humana pendiente; límites concretos del entorno"]
  }
}
```
````

El SHA identifica un commit existente y ancestro de HEAD con los mismos archivos de implementación. Un commit posterior que solo registre el informe conserva ese SHA. Sustituye el placeholder del ejemplo por el SHA observado.

Cada registro cubre todos los requisitos una vez y cada aceptación mediante `task` y `gate` (índice desde 1). Las aceptaciones también deben constar como satisfactorias en la evidencia que ejecutó el coordinador. `author.session_id` es opcional; registra la sesión real si se conoce. La autoría declarada no acredita independencia: el estado privado conserva sesión principal, delegaciones observadas y `independence: unverified`. Un entorno sin subagentes o revisión humana se declara.

`findings` admite objetos con `severity` (`low`, `medium`, `high`, `critical`), `status` (`resolved`, `accepted`), `summary` y `evidence`. Documenta la corrección o la aceptación explícita del riesgo. Las limitaciones son una lista no vacía. Si review corrige código, registra el cambio y vuelve a verificar y revisar la implementación nueva; una segunda corrección durante ese repaso bloquea el cierre.

## ENTREGA.md

Existe solo tras publicación explícita. Incluye URL de PR, estado observado de Linear y `Implementation SHA: <SHA de review>`. Si incluye `SHA: <HEAD>`, debe corresponder al HEAD observado; puede ser un commit documental posterior.

Publish solo puede escribir `ENTREGA.md`. El código, los contratos y `REVISION.md` permanecen congelados; se comprueban archivos, cambios ignorados y commits nuevos, incluso si un cambio se revierte antes de terminar. Un cambio prohibido invalida verify, review y publish. Una ejecución local completa acredita validación local; la aprobación humana y el despliegue requieren sus propios pasos.
