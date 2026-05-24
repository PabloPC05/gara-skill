---
name: commit
description: Validar y ejecutar un commit Git atomico y narrativo exclusivamente dentro del repositorio Gara. Usar cuando el usuario haya preparado staging y solicite crear el commit conforme a la politica del proyecto.
disable-model-invocation: true
argument-hint: "[contexto opcional del cambio]"
---

# Commit Gara

Crear un commit solamente cuando el usuario invoque `/gara-commit:commit`.

## Procedimiento

1. Ejecutar `git diff --cached --stat` y `git diff --cached` para comprender la intencion del staging.
2. Si el staging no representa una sola unidad logica, no ejecutar commit; indicar los archivos que deben separarse.
3. Identificar el tipo correcto entre `feat`, `fix`, `refactor` o `perf` cuando el staging contenga codigo funcional. Para cambios deterministas de documentacion, tests, estilos, build, CI o mantenimiento, dejar que el script lo infiera.
4. Redactar:
   - un titulo breve con mayuscula inicial, sin prefijo y sin punto final;
   - el contexto o la limitacion que motiva el cambio;
   - una o mas decisiones tecnicas concretas.
5. Ejecutar el validador empaquetado con esta skill:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/gara_commit.py" \
  --repo . \
  --type <tipo-si-aplica> \
  --title "<descripcion>" \
  --why "<motivo>" \
  --how "<decision tecnica>"
```

Omitir `--type` solo cuando el script pueda inferir la categoria de forma determinista. Repetir `--how` para incluir varias decisiones.

Usar primero `--dry-run` si la intencion del staging, la necesidad de documentacion o el tipo de commit requieren comprobacion adicional.

Si el usuario proporciona contexto al invocar la skill, incorporarlo solo si coincide con el diff staged:

```text
$ARGUMENTS
```

No ejecutar `git commit` directamente ni eludir un rechazo del script.
