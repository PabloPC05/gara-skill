# gara-skill

Skill de Codex para crear commits validados exclusivamente en el repositorio
[`gara`](https://github.com/PabloPC05/gara).

La skill `gara-commit` sustituye la invocacion directa de `git commit` por un
flujo que:

- valida que el staging pertenece a un checkout de `gara`;
- bloquea mezclas detectables de cambios no atomicos;
- exige documentacion staged ante cambios de API, configuracion publica,
  variables de entorno o arquitectura;
- aplica la taxonomia de commit requerida;
- construye un mensaje narrativo con `PORQUÉ`, `CÓMO` y `DOCUMENTACIÓN`;
- ejecuta `git commit` solo cuando se cumplen las validaciones.

## Instalacion En Codex

Instalar desde GitHub con la skill del sistema `skill-installer`, o ejecutar su
script auxiliar:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo PabloPC05/gara-skill `
  --path skills/gara-commit
```

Reiniciar Codex despues de instalar la skill para que aparezca como
`$gara-commit`.

## Uso

Dentro de cualquier rama del repositorio `gara`, preparar el staging y ejecutar:

```powershell
python "$env:USERPROFILE\.codex\skills\gara-commit\scripts\gara_commit.py" `
  --repo . `
  --type fix `
  --title "Corrige consulta de estado Slurm" `
  --why "La consulta podia devolver un estado tecnico sin normalizar y romper el polling del frontend." `
  --how "Normaliza los estados recibidos desde sacct." `
  --how "Cubre el caso corregido con una prueba de regresion."
```

Usar `--dry-run` para validar el staging y previsualizar el mensaje sin crear
un commit.

Para cambios cuyo tipo se deduce de forma determinista, como documentacion o
tests aislados, `--type` puede omitirse. Para cambios de codigo funcional se
debe indicar `feat`, `fix`, `refactor` o `perf`.

## Desarrollo

Validar la estructura de la skill:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py" `
  "skills\gara-commit"
```

Ejecutar las pruebas:

```powershell
python "skills\gara-commit\scripts\test_gara_commit.py" -v
```

El workflow `.github/workflows/test.yml` ejecuta estas comprobaciones en
GitHub Actions para cada `push` y `pull_request`.
