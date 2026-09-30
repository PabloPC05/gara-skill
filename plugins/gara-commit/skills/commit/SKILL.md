---
name: commit
description: Validar y ejecutar commits Git atómicos y narrativos en Gara o Gara Skill cuando el usuario invoque la skill para crear un commit conforme al staging.
disable-model-invocation: true
argument-hint: "[contexto opcional del cambio]"
---

# Commit Gara

Esta skill mantiene la invocación explícita `/gara-commit:commit`. Usa el helper empaquetado en su propio directorio y aplica las instrucciones del checkout.

## Ejecución

Ejecución directa, sin agentes. Recibe staging, intención y autorización vigente; entrega validación o commit creado mediante el helper. Si el repositorio no está admitido o hay un rechazo, explica el motivo y corrígelo dentro del alcance autorizado. No requiere delegación ni permite bypass.

## Flujo

Lee la [política compartida de commits](references/policy.md) e inspecciona `git diff --cached --stat` y `git diff --cached`. Identifica una única intención lógica y determina el tipo, título, motivo y decisiones técnicas. Todo `feat` y los cambios detectados de contratos públicos, configuración o arquitectura requieren documentación staged.

Ejecuta el helper desde el directorio real de esta skill; el plugin es autocontenido y puede cargarse desde su propio folder:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/gara_commit.py" \
  --repo . \
  --type fix \
  --title "Corrige consulta de estado" \
  --why "La consulta devolvía un estado sin normalizar y rompía la actualización de resultados." \
  --how "Normaliza el estado y cubre el caso con una prueba de regresión." \
  --dry-run
```

Omite `--type` solo para categorías que el helper pueda inferir y repite `--how` cuando haya varias decisiones. `--dry-run` previsualiza el mensaje; omítelo para crear el commit autorizado. Conserva archivos ajenos y no ejecutes `git commit` manualmente después de un rechazo. Entrega resultado y SHA real cuando corresponda; esta invocación no autoriza push, merge o despliegue.

Incorpora el contexto proporcionado al invocar la skill solo cuando concuerde con el diff staged:

```text
$ARGUMENTS
```
