# Gara Skill

Paquete de desarrollo de Gara para **Codex y Claude Code**, publicado en [PabloPC05/gara-skill](https://github.com/PabloPC05/gara-skill). Incluye 29 skills, 10 roles nativos y un ejecutor Python con aceptación comprobada, estado por spec y reanudación. Integra la skill `gara-commit` del mismo repositorio y conserva su plugin de Claude Code.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `skills/gara-*/` | Fuentes de las skills: `SKILL.md`, referencias y helpers |
| `plugins/gara-commit/` | Plugin autocontenido de commits para Claude Code |
| `roles/` | Instrucciones comunes de los 10 agentes |
| `profiles/gara.md` | Contexto Gara: stack, memoria, proceso y límites |
| `references/` | Contrato de artefactos y operación del ejecutor |
| `gara_workflow/` | Runtime, adaptadores, instalación, PDF y diagnósticos |
| `scripts/` | Entrada CLI y conversión inicial conservada |
| `tests/` | Pruebas con clientes simulados y repositorios temporales |
| `catalog.json` | Inventario y correspondencia de los 46 componentes originales |
| `.build/` | Distribuciones generadas; no se editan directamente |

La adaptación sustituye patrones Android/React Native por flujos web existentes en Gara. Usa React/Vite/TypeScript, FastAPI, pruebas vigentes y `.ai/` como memoria; los detalles del checkout y sus instrucciones prevalecen. Consulta el [catálogo y las diferencias](docs/migration.md).

## Instalación local

Necesitas Python 3.11+, Git y el CLI del motor elegido. Clona el repositorio y ejecuta:

```powershell
git clone https://github.com/PabloPC05/gara-skill.git
cd gara-skill
py scripts/gara_workflow.py validate
py scripts/gara_workflow.py install --engine both --dry-run
py scripts/gara_workflow.py install --engine both
py scripts/gara_workflow.py doctor --repo C:/ruta/gara
```

En macOS/Linux, sustituye `py` por `python3`. Codex recibe skills en `~/.agents/skills/` y agentes en `~/.codex/agents/`; Claude Code, en `~/.claude/skills/` y `~/.claude/agents/`. Abre sesiones nuevas después de instalar. No se cambian modelos, permisos ni configuración global. Si ya existe `~/.codex/skills/gara-commit`, se reutiliza y conserva.

La instalación y `--dry-run` comparten la comprobación de colisiones; el preview no escribe ni genera `.build`. Solo actualiza archivos registrados y sin modificaciones locales. Retira componentes obsoletos del motor seleccionado si mantienen su hash; una edición local bloquea antes de escribir. `--home` permite probar otro destino. `package --destination <ruta>` genera ambas distribuciones sin instalarlas. Edita las fuentes y vuelve a instalar; el helper instalado es autocontenido. La compilación refresca las copias de `profiles/gara.md` y `references/` desde sus fuentes compartidas.

Claude Code se puede instalar con `winget install --id Anthropic.ClaudeCode --exact` en Windows; inicia sesión con `claude auth login` cuando no esté autenticado. Usa `codex login status` y `claude auth status` para comprobar las cuentas. El paquete no guarda credenciales.

## Skill de commits

`gara-commit` valida el staging y crea commits narrativos en los repositorios **Gara y Gara Skill**. Revisa el diff indexado, agrupa una intención por commit y aporta documentación en cada `feat` o cambio de contrato público. El helper exige título breve y las secciones `PORQUÉ`, `CÓMO` y `DOCUMENTACIÓN`; `--dry-run` muestra el resultado sin crear el commit.

Tras instalar el paquete, invoca `$gara-commit` en Codex o `/gara-commit` en Claude Code. Si Codex reutiliza una copia previa en `~/.codex/skills/gara-commit`, esa copia conserva su versión y puede admitir solo Gara. Para desarrollar este repositorio usa el helper del checkout:

```powershell
py skills/gara-commit/scripts/gara_commit.py --repo . --type fix --title "Corrige instalación del paquete" --why "La instalación debe conservar los cambios locales del usuario." --how "Comprueba los hashes antes de actualizar archivos." --dry-run
```

Si solo necesitas el plugin de commits en Claude Code, se conserva el marketplace existente:

```text
/plugin marketplace add PabloPC05/gara-skill
/plugin install gara-commit@gara-tools
/gara-commit:commit
```

Ese plugin instala únicamente `gara-commit`; el comando `install --engine both` instala el paquete completo. La carpeta `skills/gara-commit/` sigue siendo instalable por separado mediante el instalador de skills de Codex, o copiable en `.agents/skills/` para Antigravity. Las copias del helper y sus pruebas en skill y plugin se comprueban idénticas en CI.

## Uso guiado y automático

En Codex invoca `$gara-spec`; en Claude Code, `/gara-spec`. Continúa con `gara-plan`, `gara-tasks`, `gara-build`, `gara-verify` y `gara-review`. Las skills de fases requieren invocación explícita. Las skills complementarias cubren diseño, accesibilidad, movimiento, investigación, convocatorias, logging y PDF.

Cada skill declara su entrada, salida y modo de ejecución. **8 coordinan agentes y 21 trabajan directamente**; los diez roles tienen un caso de uso explícito. Consulta la [matriz de skills y agentes](references/delegation.md) para elegirlos y comprobar sus handoffs. Las tareas pequeñas conservan ejecución directa; sin capacidad de delegación, la skill declara el fallback y sus límites. Los roles Claude disponen de `Skill` cuando lo necesitan; el revisor visual hereda las herramientas autorizadas del entorno, incluido su navegador, sin fijar servidores MCP.

El modo automático necesita una SPEC autorizada (`approved: true`), issue real `GAR-N`, rama correspondiente y checkout sin cambios ajenos. El proceso de Gara exige acreditar asignación y `In Progress` antes de implementar. No se deducen estados de Linear de un nombre de rama.

```powershell
py scripts/gara_workflow.py run --repo C:/ruta/gara --slug gar-123-mejora --engine codex --dry-run
py scripts/gara_workflow.py run --repo C:/ruta/gara --slug gar-123-mejora --engine codex
py scripts/gara_workflow.py resume --repo C:/ruta/gara --slug gar-123-mejora --engine codex
py scripts/gara_workflow.py status --repo C:/ruta/gara --slug gar-123-mejora
py scripts/gara_workflow.py metrics --repo C:/ruta/gara --slug gar-123-mejora
```

Elige `--engine claude` para Claude Code. Cada fase usa su cliente y agentes nativos; cuando no hay delegación disponible o autorizada, trabaja secuencialmente y lo declara. El coordinador ejecuta las aceptaciones y mantiene los estados; un mensaje del modelo no verifica una tarea. Los commits pasan por `gara-commit`.

`run` termina con validación y revisión local. Añade `--publish` solo para publicar la rama, abrir/reutilizar la PR y pasar a `In Review` mediante capacidades autenticadas. La revisión humana exigida por Gara sigue pendiente. No se lanzan trabajos HPC reales al probar la herramienta.

Verify y review exigen evidencia estructurada ligada al SHA de implementación. Publish solo escribe `ENTREGA.md`: cualquier cambio en código o artefactos cerrados invalida el cierre. El lock abarca todo el checkout, aunque se usen slugs distintos. Una sesión principal o un nombre de agente en el informe no acreditan revisión independiente.

Los artefactos viven en `specs/<slug>/`; el estado, locks y resúmenes en el directorio Git privado. Tras escribir `TAREAS.md` el ejecutor se detiene para que una persona revise los comandos de aceptación que lanzará fuera del sandbox del cliente; un checkpoint se reanuda con `--ack-checkpoint` tras revisión real (se puede dar desde el primer `run`). Si el estado queda irrecuperable tras un merge o rebase, `reset --repo <ruta> --slug <slug> --yes` borra solo el estado privado, no `specs/`. Véanse [contrato de artefactos](references/artifacts.md) y [operación, permisos y recuperación](references/runtime.md). Salidas: 0 éxito/dry-run, 2 bloqueo, 1 fallo, 130 interrupción (también SIGTERM y SIGHUP).

## Desarrollo y pruebas

El runtime utiliza la biblioteca estándar. PyYAML es opcional para validar metadatos con herramientas externas; ffmpeg, numpy/scipy/OpenCV sirven para helpers de análisis de vídeo. PDF requiere Chrome/Chromium/Edge local y usa fuentes y logo embebidos.

Ruff proporciona un único formatter y linter para el código Python propio; su configuración está en `pyproject.toml`. Los originales y helpers externos conservados quedan excluidos. Para preparar desarrollo: `py -m venv .venv` y `.venv/Scripts/python -m pip install -e ".[dev,validation]"`.

En macOS/Linux, usa `.venv/bin/python` en los comandos del entorno virtual.

```powershell
py -m unittest discover -s tests -v
py skills/gara-commit/scripts/test_gara_commit.py -v
py plugins/gara-commit/skills/commit/scripts/test_gara_commit.py -v
py scripts/gara_workflow.py validate
py scripts/gara_workflow.py package
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

Las pruebas ejecutan comandos de aceptación reales en repositorios temporales, sin servicios científicos, credenciales, Linear ni publicación. Los simuladores comprueban contratos y recuperación; no equivalen a una ejecución real de modelos ni a CI remoto. El ejemplo PDF se genera con `skills/gara-pdf/scripts/build_pdf.py` y recursos de esa skill.

GitHub Actions ejecuta la suite, Ruff, validación del catálogo y construcción e instalación en un destino temporal. El clon contiene las fuentes y recursos necesarios; `export.zip` y `export/` se conservan solo en el checkout original y no se necesitan para instalar. `AGENTS.md` permanece sin modificaciones.

El [registro de validación](docs/validation.md) documenta resultados, detección nativa y límites observados. La [auditoría y sus correcciones](docs/audit/README.md) conservan las observaciones iniciales y enlazan las regresiones posteriores.

Para una entrada CLI editable opcional: `py -m pip install -e .`, después `gara-workflow doctor`. La generación e instalación del paquete de skills se realizan desde este checkout; no se ofrece un wheel independiente de recursos. Usa cuatro espacios en Python y `ruff format`, formato Markdown sencillo y cambios de una intención. Conserva licencias y [procedencia](docs/provenance.md); no añadas secretos o rutas personales a los defaults.
