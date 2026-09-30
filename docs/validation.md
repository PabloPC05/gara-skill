# Validación de la adaptación

Comprobaciones del 1 de octubre de 2026 en Windows, con Python 3.13.15, Codex CLI 0.159.1 y Claude Code 2.1.286. El runtime exige Python 3.11+; otras plataformas no se probaron aquí. La [auditoría](audit/README.md) conserva el diagnóstico inicial y sus [correcciones](audit/corrections.md).

## Paquete e instalación

- Catálogo: 29 skills, 10 agentes y correspondencia de los 46 componentes originales.
- Skill-creator: 29 fuentes y 29 variantes Codex válidas; formatos de los 20 agentes generados comprobados.
- Instalación local: 340 archivos gestionados. Codex recibe 28 skills y reutiliza `gara-commit`; Claude recibe 29. Reinstalar informa cero cambios y retiradas: [installation-final.json](audit/installation-final.json).
- Ocho skills coordinadas y 21 directas; diez roles con casos de uso en la [matriz](../references/delegation.md). Se conservan 15 políticas explícitas y modelos heredados.

## Ejecutor

La suite completa pasó **119 pruebas en 643,447 segundos**, con 64 regresiones nuevas: 30 del ejecutor, 20 de instalación y 14 de protocolos/persistencia. La validación inicial había pasado 55 pruebas. Ruff 0.16.9 pasó lint y comprobación de formato.

```powershell
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python docs/audit/reproduce.py
.venv/Scripts/python scripts/gara_workflow.py validate
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

Las [siete reproducciones repetidas](audit/resolution.json) confirman sus correcciones. Las regresiones cubren entrega congelada, índice y commits/reverts, SHA ligado a blobs Git, evidencia estructurada, invalidación/reanudación, locks entre procesos y worktrees, issues exactos, redacción JSON/escapada, metadatos de delegación y preflight/retirada por hash. Los clientes simulados ejecutan aceptaciones reales en temporales.

## Clientes reales y PDF

Ambos clientes autenticados completaron una lectura de `catalog.json` y `skills/gara-plan/SKILL.md`, explicando correctamente sus agentes y fallback. [native_smoke.py](audit/native_smoke.py) reproduce esas lecturas; resultados normalizados en `output/validation/native/`.

Claude utilizó el rol nativo `gara-scout`; su inicialización registró 29 skills y 10 agentes. Ese rol no necesita `Skill`, por lo que su ausencia en su listado es esperada. Codex declaró una devolución de scout, pero el adaptador no observó eventos de delegación interpretables: la afirmación no acredita identidad ni independencia. El estado conserva `independence: unverified`.

Estas lecturas no ejercitan todas las skills/roles ni prueban navegador, publicación, CI remoto o una feature real. La prueba anterior de Claude del 30 de septiembre devolvió `Not logged in`; ahora estaba autenticado.

El PDF inicial de `output/pdf/` conserva contenido ficticio, Lato y logo embebidos, texto extraído y dos páginas inspeccionadas. Las pruebas actuales comprueban composición y escape de metadatos.

## Conservación y límites

`AGENTS.md` conserva SHA-256 `0386f157665fd76eac130c28d4dabfa45f443eacc2ce14a53a5563f543dd5cb1`. El ZIP mantiene su hash y los 80 originales coinciden byte a byte. Los enlaces y sintaxis se comprobaron.

Esta revisión no escribió en Gara. Doctor observó HEAD `43c44e1ad94dda4f0f9f2ff04fc0972b16fa065c`; el HEAD histórico era `e4747838db0c7c76eca51348a6684bfb9e5a187c`. No se publicó una PR, modificó Linear ni ejecutó HPC o despliegues.

Los guards comprueban al regresar el cliente y conservan cambios bloqueados para reconciliación. No revierten automáticamente ni certifican que un efecto remoto haya sido evitado. Los informes antiguos sin `gara-review:v1` requieren nueva evidencia real antes de cerrar.

## Integración para GitHub

Se integró `gara-commit` desde el SHA `41d79264ad555721491958067e82a8169c2c72de` de [PabloPC05/gara-skill](https://github.com/PabloPC05/gara-skill), conservando su historial, marketplace y plugin. La versión 1.2.0 admite Gara y Gara Skill; helper, pruebas y política son idénticos en skill y plugin. Pasaron 34 pruebas acotadas: 12 de cada copia y 10 regresiones nuevas con repositorios temporales. La validación nativa del plugin de Claude también pasó.

Pasaron 24 comprobaciones de instalación: dos de publicación sin archivo histórico, dos del setup de Packaging sin `export/` y 20 regresiones de instalación. El smoke construye e instala ambos motores en temporales, retira la fuente y ejecuta los helpers instalados; utiliza clientes inexistentes para evitar llamadas a modelos. La exportación opcional sigue comprobando cobertura del catálogo.

Las 29 fuentes Codex y el frontmatter Claude del plugin se validaron; Ruff comprobó 130 archivos y los 211 enlaces locales existen. Se verificaron de nuevo los hashes protegidos y la identidad de los 80 originales. La suite publicada contiene 131 casos; GitHub Actions la ejecuta en Ubuntu/Python 3.12 junto con los checks de commits, Ruff y catálogo. Estos resultados acotados complementan la ejecución local completa de 119 casos registrada arriba.
