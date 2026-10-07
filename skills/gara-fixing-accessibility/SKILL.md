---
name: "gara-fixing-accessibility"
description: "Verifica y corrige foco, orden de teclado, contraste y semántica accesible en pantallas web de Gara; usar al revisar o arreglar un problema de accesibilidad concreto, no para un pulido visual general (gara-baseline-ui)."
---

# Accesibilidad Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe controles o flujos y su reproducción; entrega hallazgos o correcciones de semántica, foco, teclado y contraste con evidencia. Si falta navegador o tecnología asistiva, declara qué no se comprobó. Aplica los criterios solo al alcance pedido y al sistema visual existente: sin dependencias nuevas ni rediseño incidental. Al terminar, devuelve el resultado y espera instrucciones; no encadena otras skills ni hace commit.

## Uso

- `/gara-fixing-accessibility`: aplica estos criterios al trabajo de UI de la conversación.
- `/gara-fixing-accessibility <archivo>`: revisa el archivo contra las reglas y para cada hallazgo da la línea o fragmento exacto, por qué importa (una frase) y una corrección concreta.

Prefiere correcciones mínimas y localizadas; no reescribas partes grandes de la UI.

## Cuándo aplicar

- Botones, enlaces, inputs, menús, diálogos, pestañas o desplegables nuevos o modificados.
- Formularios, validación, errores y textos de ayuda.
- Atajos de teclado o interacciones personalizadas.
- Foco, trampas de foco y comportamiento modal.
- Controles solo con icono, interacciones solo con hover o contenido oculto.

## Prioridad de las reglas

| prioridad | categoría | impacto |
|-----------|-----------|---------|
| 1 | nombres accesibles | crítico |
| 2 | acceso por teclado | crítico |
| 3 | foco y diálogos | crítico |
| 4 | semántica | alto |
| 5 | formularios y errores | alto |
| 6 | anuncios | medio-alto |
| 7 | contraste y estados | medio |
| 8 | medios y movimiento | bajo-medio |
| 9 | límites de la herramienta | crítico |

### 1. Nombres accesibles (crítico)

- Todo control interactivo tiene nombre accesible.
- Los botones solo con icono llevan `aria-label` o `aria-labelledby`.
- Todo input, select y textarea está etiquetado.
- Los enlaces tienen texto con sentido (nada de "pulsa aquí").
- Los iconos decorativos llevan `aria-hidden`.

### 2. Teclado (crítico)

- No uses `div` o `span` como botón sin soporte completo de teclado.
- Todo elemento interactivo es alcanzable con Tab y muestra foco visible.
- No uses `tabindex` mayor que 0.
- Escape cierra diálogos y overlays cuando corresponde.

### 3. Foco y diálogos (crítico)

- Los modales atrapan el foco mientras están abiertos, lo colocan dentro al abrir y lo devuelven al disparador al cerrar.
- Abrir un diálogo no debe desplazar la página de forma inesperada.

### 4. Semántica (alto)

- Prefiere elementos nativos (`button`, `a`, `input`) a roles improvisados; si usas un rol, incluye sus atributos aria obligatorios.
- Las listas usan `ul`/`ol` con `li`; no saltes niveles de encabezado; las tablas usan `th` en las cabeceras.

### 5. Formularios y errores (alto)

- Vincula errores y ayudas a su campo con `aria-describedby`; marca `aria-invalid` en los inválidos y anuncia los obligatorios.
- Un envío deshabilitado explica por qué.

### 6. Anuncios (medio-alto)

- Los errores críticos de formulario usan `aria-live`; las cargas, `aria-busy` o texto de estado.
- Un toast no es la única vía para información crítica.
- Los controles expandibles usan `aria-expanded` y `aria-controls`.

### 7. Contraste y estados (medio)

- Contraste suficiente en texto e iconos; el estado deshabilitado no depende solo del color.
- Toda interacción solo con hover tiene equivalente de teclado.
- No quites el contorno de foco sin un sustituto visible.

### 8. Medios y movimiento (bajo-medio)

- Las imágenes tienen alt correcto (descriptivo o vacío); los vídeos con voz, subtítulos cuando proceda.
- Respeta `prefers-reduced-motion` en el movimiento no esencial; no reproduzcas audio automáticamente.

### 9. Límites de la herramienta (crítico)

- Cambios mínimos; no refactorices código ajeno al problema.
- No añadas aria cuando la semántica nativa ya lo resuelve.
- No migres librerías de UI salvo petición expresa; en widgets complejos (menú, diálogo, combobox) prefiere las primitivas accesibles ya usadas en el checkout.

## Correcciones habituales

```html
<!-- botón solo con icono: añade aria-label -->
<!-- antes -->   <button><svg>...</svg></button>
<!-- después --> <button aria-label="Cerrar"><svg aria-hidden="true">...</svg></button>

<!-- div como botón: usa el elemento nativo -->
<!-- antes -->   <div onclick="save()">Guardar</div>
<!-- después --> <button onclick="save()">Guardar</button>

<!-- error de formulario: vincúlalo con aria-describedby -->
<!-- antes -->   <input id="email" /> <span>Correo no válido</span>
<!-- después --> <input id="email" aria-describedby="email-err" aria-invalid="true" /> <span id="email-err">Correo no válido</span>
```

## Orden de trabajo

Arregla primero lo crítico (nombres, teclado, foco, límites). Cita el fragmento exacto, indica el fallo y propón un arreglo pequeño.
