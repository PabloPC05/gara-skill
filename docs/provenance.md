# Procedencia y licencias

`export.zip` es la copia proporcionada por el usuario de `Downloads/export.zip`; `export/` conserva sus 80 archivos útiles originales en el checkout inicial. Ambos se preservan localmente y se excluyen de Git. El paquete publicado incluye las fuentes adaptadas y sus recursos; usar el paquete no requiere la exportación. La conversión inicial se hizo con un script que ya no existe (véase el historial de Git); las mejoras posteriores se hacen directamente en las fuentes canónicas.

Las referencias y helpers de `ui-animation`, y las guías reutilizables de interfaz y accesibilidad, proceden de esa exportación. Se conserva `skills/gara-frontend-design/LICENSE.txt`. La ausencia de otra licencia expresa no se sustituye por una licencia inventada; comprueba los derechos antes de una distribución pública.

La fuente del validador de commits es [PabloPC05/gara-skill](https://github.com/PabloPC05/gara-skill/tree/41d79264ad555721491958067e82a8169c2c72de), SHA `41d79264ad555721491958067e82a8169c2c72de`. Se importan sus helpers, pruebas, metadatos y plugin, conservando el historial Git. La adaptación admite Gara Skill además de Gara, mantiene la documentación obligatoria en cada `feat` y sincroniza las copias ejecutables de `skills/gara-commit/` y `plugins/gara-commit/`. El plugin conserva el marketplace `gara-tools` y `/gara-commit:commit`.

Para commitear este paquete se usa el helper de su checkout. Los recursos gráficos, fuentes y licencias del PDF se detallan en [su procedencia](../skills/gara-pdf/assets/PROVENANCE.md).

El perfil Gara deriva del checkout local observado, HEAD `e4747838db0c7c76eca51348a6684bfb9e5a187c`: instrucciones raíz, `.ai/`, documentación de Linear, manifiestos y código frontend/backend. No afirma que otras ramas conserven ese inventario. Las fuentes oficiales sobre el formato de skills y agentes están en [el flujo](../references/flujo.md#fuentes).
