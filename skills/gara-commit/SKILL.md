---
name: gara-commit
description: Validar y ejecutar commits Git atomicos y narrativos exclusivamente en el repositorio Gara. Usar cuando un desarrollador o agente solicite hacer commit, preparar un commit, validar el staging antes de commitear o sustituir `git commit` dentro de cualquier rama de `gara`.
---

# Gara Commit

Usar `scripts/gara_commit.py` en lugar de invocar `git commit` directamente.

## Flujo

1. Inspeccionar el staging con `git diff --cached --stat` y `git diff --cached`.
2. Determinar una unica intencion logica para el cambio. Si existen intenciones distintas, detenerse y pedir que se reindexen por separado.
3. Elegir el tipo semantico:
   - `feat`: nueva funcionalidad.
   - `fix`: correccion de error.
   - `refactor`: reestructuracion sin cambio externo.
   - `perf`: rendimiento.
   - `test`: solo pruebas.
   - `style`: solo formato o estetica.
   - `docs`: solo documentacion o comentarios.
   - `build`: dependencias o empaquetado.
   - `ci`: pipeline, despliegue o Docker.
   - `chore`: mantenimiento sin codigo ni tests.
4. Redactar una descripcion de hasta 50 caracteres, iniciada en mayuscula y sin punto final.
5. Redactar el motivo y las decisiones tecnicas reales del diff.
6. Ejecutar el script desde cualquier subdirectorio del checkout de Gara:

```powershell
python "$env:USERPROFILE\.codex\skills\gara-commit\scripts\gara_commit.py" `
  --repo . `
  --type fix `
  --title "Corrige consulta de estado Slurm" `
  --why "La consulta podia devolver un estado tecnico sin normalizar y romper el polling del frontend." `
  --how "Normaliza los estados recibidos desde sacct en backend/src/utils/slurmState.js." `
  --how "Cubre el caso corregido con una prueba de regresion."
```

Usar `--dry-run` para validar y mostrar el mensaje sin crear el commit.

## Reglas Del Ejecutable

- Abortar fuera de un checkout identificado como `gara` por su raiz o remoto.
- Abortar sin archivos indexados.
- Bloquear mezclas detectables de codigo funcional y estilos, o de categorias independientes.
- Requerir documentacion staged si el diff muestra cambios de API, variables de entorno, configuracion publica o arquitectura.
- Inferir tipos deterministas (`docs`, `test`, `style`, `build`, `ci`, `chore`). Para cambios de codigo, exigir `--type feat|fix|refactor|perf` porque la intencion no se puede derivar fiablemente del texto del diff.
- Construir siempre las secciones `PORQUÉ`, `CÓMO` y `DOCUMENTACIÓN`; listar automaticamente la documentacion staged o `N/A`.

No usar opciones de bypass ni ejecutar `git commit` manualmente tras un rechazo del script. Corregir el staging o la documentacion y volver a validar.
