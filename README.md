# gara-skill

Skill para Codex y Google Antigravity, y plugin para Claude Code, que crean commits validados
exclusivamente en el repositorio
[`gara`](https://github.com/PabloPC05/gara).

La skill `gara-commit` sustituye la invocacion directa de `git commit` por un
flujo que:

- valida que el staging pertenece a un checkout de `gara`;
- bloquea mezclas detectables de cambios no atomicos;
- exige documentacion staged para todo `feat` y ante cambios de API,
  configuracion publica, variables de entorno o arquitectura;
- aplica la taxonomia de commit requerida;
- construye un mensaje narrativo con `PORQUÉ`, `CÓMO` y `DOCUMENTACIÓN`;
- ejecuta `git commit` solo cuando se cumplen las validaciones.

## Instalacion En Claude Code

La distribucion recomendada para Claude Code es el plugin `gara-commit`
publicado en el marketplace `gara-tools` de este repositorio:

```text
/plugin marketplace add PabloPC05/gara-skill
/plugin install gara-commit@gara-tools
```

La skill se invoca manualmente porque crea commits:

```text
/gara-commit:commit
```

Se puede proporcionar contexto adicional, que Claude debe contrastar con el
staging antes de usarlo:

```text
/gara-commit:commit Corrige la normalizacion de estados Slurm
```

Para probar el plugin desde un checkout local:

```powershell
claude --plugin-dir ".\plugins\gara-commit"
```

La estructura del plugin sigue la documentacion oficial de
[Claude Code Skills](https://code.claude.com/docs/en/skills) y
[Claude Code Plugins](https://code.claude.com/docs/en/plugins).
Las nuevas publicaciones del plugin deben incrementar la version semantica de
`plugins/gara-commit/.claude-plugin/plugin.json` para que Claude Code detecte
la actualizacion.

## Instalacion En Google Antigravity

Antigravity utiliza skills con `SKILL.md`. El paquete
`skills/gara-commit/` de este repositorio es compatible directamente con sus
dos ubicaciones oficiales.

Instalacion global para todos los workspaces del usuario:

```powershell
$temp = Join-Path ([IO.Path]::GetTempPath()) ("gara-skill-" + [guid]::NewGuid().ToString("N"))
git clone --depth 1 https://github.com/PabloPC05/gara-skill.git $temp
$dest = "$env:USERPROFILE\.gemini\antigravity\skills\gara-commit"
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Recurse -Force "$temp\skills\gara-commit\*" $dest
Remove-Item -LiteralPath $temp -Recurse -Force
```

Instalacion limitada a un checkout concreto de `gara`:

```powershell
cd C:\ruta\a\gara
$temp = Join-Path ([IO.Path]::GetTempPath()) ("gara-skill-" + [guid]::NewGuid().ToString("N"))
git clone --depth 1 https://github.com/PabloPC05/gara-skill.git $temp
$dest = ".agents\skills\gara-commit"
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item -Recurse -Force "$temp\skills\gara-commit\*" $dest
Remove-Item -LiteralPath $temp -Recurse -Force
```

Antigravity selecciona la skill a partir de su descripcion. El usuario puede
pedirle al agente que use `gara-commit` para crear el commit staged.

La estructura sigue la documentacion oficial de
[Google Antigravity Agent Skills](https://antigravity.google/docs/skills).
Google indica que `.agents/skills/` es la ruta de workspace vigente y que
`.agent/skills/` se conserva solo por compatibilidad.

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

## Uso Del Script

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

En una instalacion global de Antigravity, sustituir la ruta del script por:

```powershell
python "$env:USERPROFILE\.gemini\antigravity\skills\gara-commit\scripts\gara_commit.py" `
  --repo . `
  --type fix `
  --title "Corrige consulta de estado Slurm" `
  --why "La consulta podia devolver un estado tecnico sin normalizar y romper el polling del frontend." `
  --how "Normaliza los estados recibidos desde sacct."
```

En una instalacion Antigravity del workspace `gara`, usar:

```powershell
python ".agents\skills\gara-commit\scripts\gara_commit.py" `
  --repo . `
  --type fix `
  --title "Corrige consulta de estado Slurm" `
  --why "La consulta podia devolver un estado tecnico sin normalizar y romper el polling del frontend." `
  --how "Normaliza los estados recibidos desde sacct."
```

Usar `--dry-run` para validar el staging y previsualizar el mensaje sin crear
un commit.

Para cambios cuyo tipo se deduce de forma determinista, como documentacion o
tests aislados, `--type` puede omitirse. Para cambios de codigo funcional se
debe indicar `feat`, `fix`, `refactor` o `perf`.

Todo `feat` debe incluir en staging al menos un archivo Markdown o un archivo
de una carpeta `docs/`. La misma exigencia se aplica si el script detecta
cambios de API, configuracion publica, variables de entorno o arquitectura.

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
GitHub Actions para cada `push` y `pull_request`, tanto para el paquete Codex
como para el plugin Claude Code.
