---
name: gara-commit
description: Validar y ejecutar commits Git atómicos y narrativos en Gara o Gara Skill; usar cuando se solicite crear o preparar un commit, revisar el staging o sustituir git commit en uno de esos checkouts.
disable-model-invocation: true
---

# Gara Commit

Usa `scripts/gara_commit.py`, resuelto respecto a esta skill, en lugar de invocar `git commit` directamente. Aplica las instrucciones del checkout; para Gara consulta el [perfil Gara](references/gara.md), y para Gara Skill conserva sus instrucciones de repositorio.

## Ejecución

Ejecución directa, sin agentes. Recibe staging, intención y autorización vigente; entrega validación o commit creado mediante el helper. Si no hay un repositorio admitido o el helper rechaza el cambio, explica el motivo y corrígelo dentro del alcance autorizado. No requiere delegación ni permite bypass.

## Flujo

Lee la [política compartida de commits](references/policy.md), inspecciona el diff staged e identifica una única intención. Elige el tipo semántico y redacta título, motivo y decisiones técnicas basados en ese diff. Todo `feat` y los cambios detectados de contratos públicos, configuración o arquitectura requieren documentación staged.

Obtén la ruta real del directorio que contiene este `SKILL.md`; los ejemplos no dependen de una instalación global concreta. Sustituye los marcadores por esa ruta y por el checkout objetivo:

```powershell
python "<directorio-de-la-skill>/scripts/gara_commit.py" `
  --repo "<checkout-de-gara-o-gara-skill>" `
  --type fix `
  --title "Corrige consulta de estado" `
  --why "La consulta devolvía un estado sin normalizar y rompía la actualización de resultados." `
  --how "Normaliza el estado y cubre el caso con una prueba de regresión." `
  --dry-run
```

Omite `--type` solo para categorías que el helper pueda inferir y repite `--how` cuando haya varias decisiones. `--dry-run` previsualiza el mensaje; omítelo para crear el commit autorizado. Conserva archivos ajenos y no ejecutes `git commit` manualmente después de un rechazo. Entrega resultado y SHA real cuando corresponda; publicar la rama requiere su autorización propia.
