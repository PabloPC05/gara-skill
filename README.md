# Gara Skill

Skills y agentes de **Claude Code** para desarrollar Gara, publicados en [PabloPC05/gara-skill](https://github.com/PabloPC05/gara-skill). Son 28 skills y 11 agentes. No hay ejecutor ni automatización: tú invocas cada fase y decides cuándo pasar a la siguiente. Incluye `gara-commit`, también disponible como plugin independiente.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `skills/gara-*/` | Una carpeta por skill: `SKILL.md`, referencias y helpers propios |
| `agents/` | Los 11 agentes, con frontmatter nativo de Claude Code |
| `profiles/gara.md` | Contexto Gara: stack, memoria, proceso y límites |
| `references/` | Flujo manual, casos de uso, contrato de artefactos y matriz de delegación |
| `plugins/gara-commit/` | Plugin autocontenido de commits (marketplace `gara-tools`) |
| `scripts/check.sh` | Comprueba frontmatter, copias de referencias y enlaces |

Cada skill lleva copias de `profiles/gara.md` y de las referencias que enlaza en su carpeta `references/`, para funcionar una vez instalada. **Edita siempre los originales** y vuelve a copiar:

```bash
for d in skills/*/; do
  cp profiles/gara.md "$d/references/gara.md" 2>/dev/null
  for f in flujo artifacts delegation casos-de-uso; do
    [ -f "$d/references/$f.md" ] && cp "references/$f.md" "$d/references/"
  done
done
bash scripts/check.sh
```

## Instalación

Copia las skills y los agentes a tu configuración de Claude Code y abre una sesión nueva:

```powershell
Copy-Item -Recurse skills\* $HOME\.claude\skills\
Copy-Item agents\* $HOME\.claude\agents\
```

Para limitarlos a un proyecto, usa `.claude/skills/` y `.claude/agents/` de ese checkout. Solo `gara-commit` se instala también como plugin:

```text
/plugin marketplace add PabloPC05/gara-skill
/plugin install gara-commit@gara-tools
```

## Cómo se trabaja

Las skills de fase solo se ejecutan si las invocas (`disable-model-invocation`). Cada una hace un único paso, escribe su artefacto en `specs/<slug>/` del checkout de Gara y se detiene con un resumen y la decisión que te toca:

`/gara-spec` → `/gara-plan` → `/gara-tasks` → `/gara-build` → `/gara-verify` → `/gara-review` → `/gara-deliver`

Tú apruebas la SPEC, lees el plan, revisas las tareas y sus comandos de aceptación antes de construir, y ordenas explícitamente cada commit (`/gara-commit`) y la publicación. **¿Qué skills y agentes uso para una feature, un bug, una pantalla o una investigación?** Consulta los [casos de uso](references/casos-de-uso.md), o invoca `/gara-workflow` para que te oriente. Detalles en [references/flujo.md](references/flujo.md), formato de los artefactos en [references/artifacts.md](references/artifacts.md) y cuándo se delega a un agente en [references/delegation.md](references/delegation.md).

`/gara-probar` recorre una feature en un navegador real con [browser-harness](skills/gara-probar/references/navegador.md) (Browser Use); la guía explica cómo instalarlo y por qué usar un Chrome dedicado. Las skills complementarias cubren diseño, accesibilidad, movimiento, investigación, convocatorias, logging y PDF. Las no explícitas pueden activarse solas cuando la petición encaja con su descripción.

## Skill de commits

`gara-commit` valida el staging y crea commits narrativos en Gara y en este repositorio: título breve y secciones `PORQUÉ`, `CÓMO` y `DOCUMENTACIÓN`. `--dry-run` muestra el resultado sin crearlo.

```powershell
py skills/gara-commit/scripts/gara_commit.py --repo . --type fix --title "Corrige un fallo" --why "Motivo." --how "Cambio." --dry-run
```

El helper y sus pruebas existen en dos copias idénticas (`skills/gara-commit/scripts/` y `plugins/gara-commit/skills/commit/scripts/`); `scripts/check.sh` lo comprueba.

## Pruebas

```powershell
bash scripts/check.sh
py skills/gara-commit/scripts/test_gara_commit.py -v
py plugins/gara-commit/skills/commit/scripts/test_gara_commit.py -v
```

`gara-pdf` necesita Chrome, Chromium o Edge local; usa Lato y el logo de Gara embebidos. Los helpers de análisis de vídeo de `gara-ui-animation` usan ffmpeg, numpy/scipy y OpenCV. Consulta [la procedencia de las skills importadas](docs/provenance.md) y [el historial de la adaptación](docs/migration.md).
