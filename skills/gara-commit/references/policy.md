# Política de commits de Gara y Gara Skill

Lee el diff staged y las instrucciones del checkout antes de elegir el mensaje. Una única intención lógica puede incluir código, sus pruebas y su documentación. El helper detecta mezclas por categorías; la coherencia semántica del cambio se comprueba al leer el diff.

## Repositorios admitidos

El helper acepta únicamente un checkout cuya raíz se llame `gara` o `gara-skill`, o cuyo `remote.origin.url` termine exactamente en uno de esos nombres, con sufijo `.git` opcional. Resuelve el repositorio desde cualquier subdirectorio. Un remoto secundario o nombres como `gara-skill-extra` no habilitan el comando. No existe una opción de bypass.

## Staging y tipo

Inspecciona `git diff --cached --stat` y `git diff --cached`; añade solo archivos de la intención autorizada y conserva cambios ajenos. Sin archivos staged, el helper rechaza el commit.

El helper bloquea código funcional mezclado con estilos y categorías independientes. Código y cambios de build que sirven a la misma intención pueden ir juntos, acompañados de sus pruebas y documentación; revisa que realmente pertenezcan al mismo cambio.

| Tipo | Intención |
| --- | --- |
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de error |
| `refactor` | Reestructuración sin cambio externo |
| `perf` | Rendimiento |
| `test` | Pruebas |
| `style` | Formato o estética |
| `docs` | Documentación |
| `build` | Dependencias o empaquetado |
| `ci` | Pipeline, despliegue o Docker |
| `chore` | Mantenimiento |

Las categorías deterministas permiten omitir `--type`. Para código, indica `feat`, `fix`, `refactor` o `perf` según la intención; no uses `chore` para eludir esta selección. Los tests bajo `test/`, `tests/`, con prefijo `test_` o con sufijos `.test.`/`.spec.` se clasifican como pruebas.

## Documentación y mensaje

Todo `feat` requiere documentación staged. El helper también la exige ante cambios detectados de API pública, variables de entorno, configuración pública o arquitectura, aunque el tipo sea otro. Cuenta cualquier archivo Markdown o ruta bajo `docs/`; un archivo presente solo en el árbol de trabajo no satisface la regla. La documentación debe explicar el cambio real.

La descripción de `--title` tiene como máximo 50 caracteres, comienza con mayúscula y no termina en punto. No incluyas el prefijo semántico: lo genera el helper. `--why` explica el motivo y cada `--how` una decisión real del diff; se puede repetir `--how`.

El mensaje siempre contiene `PORQUÉ`, `CÓMO` y `DOCUMENTACIÓN`. El helper lista la documentación staged o escribe `N/A` cuando la política no la requiere y no hay documentación.

## Ejecución y rechazo

Resuelve `scripts/gara_commit.py` respecto al directorio de esta skill. Requiere Python 3.11 o superior y Git; usa la identidad Git y los hooks existentes del checkout. No cambia configuración global.

`--dry-run` valida y muestra el mensaje sin crear un commit. Para crear el commit, omite esa opción solo dentro de la autorización vigente. La invocación no autoriza push, merge o despliegue.

Si el helper rechaza el staging, tipo, título o documentación, corrige el motivo y vuelve a validar. No ejecutes `git commit` manualmente ni desactives validaciones o hooks para continuar. Devuelve el mensaje/rechazo real y, si se creó un commit, su SHA.
