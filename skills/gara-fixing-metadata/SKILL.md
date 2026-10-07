---
name: "gara-fixing-metadata"
description: "Corrige título, descripción, canonical, Open Graph y otros metadatos HTML del alcance publicado de la web de Gara; usar cuando se describa un problema de metadatos o de previsualización al compartir."
---

# Metadatos web Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe página o alcance publicado, contenido e identidad verificados; entrega metadatos y las comprobaciones pertinentes. Si falta acceso a la versión publicada, distingue el cambio local de su validación remota. Aplica los criterios solo al alcance pedido: sin dependencias nuevas ni rediseño incidental. Al terminar, devuelve el resultado y espera instrucciones; no publica, despliega ni hace commit.

## Flujo

1. Identifica las páginas con metadatos ausentes o incorrectos (título, descripción, canonical, etiquetas OG).
2. Audita contra las reglas de prioridad y arregla primero lo crítico (duplicados, indexación).
3. Asegura que título, descripción, canonical y `og:url` concuerdan entre sí.
4. Valida las tarjetas sociales en una URL real, no en localhost, usando un despliegue ya autorizado; no publiques solo para probar.
5. Mantén el diff mínimo y limitado a metadatos; no refactorices código ajeno.

## Cuándo aplicar

- Títulos, descripciones, canonical o robots nuevos o modificados.
- Open Graph o Twitter cards.
- Favicons, iconos, manifest o `theme-color`.
- Componentes o valores por defecto de metadatos compartidos.
- Datos estructurados (JSON-LD).
- Idioma, alternates o rutas canónicas.
- Páginas nuevas o enlaces para compartir.

## Prioridad de las reglas

| prioridad | categoría | impacto |
|-----------|-----------|---------|
| 1 | corrección y duplicados | crítico |
| 2 | título y descripción | alto |
| 3 | canonical e indexación | alto |
| 4 | tarjetas sociales | alto |
| 5 | iconos y manifest | medio |
| 6 | datos estructurados | medio |
| 7 | idioma y alternates | bajo-medio |
| 8 | límites de la herramienta | crítico |

### 1. Corrección y duplicados (crítico)

- Define los metadatos en un solo lugar por página; evita sistemas competidores.
- No emitas `title`, `description`, `canonical` ni `robots` duplicados.
- Valores deterministas, sin aleatoriedad ni inestabilidad.
- Escapa y sanea las cadenas dinámicas o generadas por usuarios.
- Toda página tiene título y descripción por defecto seguros.

### 2. Título y descripción (alto)

- Toda página tiene título, con formato consistente en el sitio, corto y legible, sin relleno de palabras clave.
- Las páginas compartibles o indexables llevan meta description en texto plano (sin markdown ni comillas de más).

### 3. Canonical e indexación (alto)

- El canonical apunta a la URL preferida de la página.
- `noindex` solo en páginas privadas, duplicadas o no públicas; los previews y staging, `noindex` por defecto cuando sea posible.
- `robots` refleja la intención real de acceso; las páginas paginadas, un canonical correcto.

### 4. Tarjetas sociales (alto)

- Las páginas compartibles fijan título, descripción e imagen de Open Graph.
- Las imágenes OG y Twitter usan URLs absolutas, con dimensiones y proporción estables.
- `og:url` coincide con el canonical; `og:type` razonable (normalmente `website` o `article`); `twitter:card` apropiado (`summary_large_image` por defecto).

### 5. Iconos y manifest (medio)

- Al menos un favicon que funcione entre navegadores; `apple-touch-icon` si procede.
- Manifest válido y referenciado cuando se use; `theme-color` intencional, que no desentone con la UI.
- Rutas de iconos estables y cacheables.

### 6. Datos estructurados (medio)

- No añadas JSON-LD si no corresponde claramente al contenido real; debe ser válido y reflejar lo renderizado.
- No inventes valoraciones, reseñas, precios ni datos de organización.
- Un bloque por página salvo necesidad.

### 7. Idioma y alternates (bajo-medio)

- `lang` del html correcto; `og:locale` si hay localización.
- `hreflang` solo si las páginas existen; las localizadas canonicalizan por idioma.

### 8. Límites de la herramienta (crítico)

- Cambios mínimos; no refactorices código ajeno.
- No migres frameworks ni librerías SEO salvo petición expresa.
- Sigue el patrón de metadatos del checkout (react-helmet, `<head>` manual en `index.html` o un helper propio); Gara es una SPA Vite, no Next.js.

## Orden de trabajo

Arregla primero lo crítico (duplicados, canonical, indexación). Que título, descripción, canonical y `og:url` coincidan. Prefiere metadatos estables y aburridos a los ingeniosos o dinámicos.
