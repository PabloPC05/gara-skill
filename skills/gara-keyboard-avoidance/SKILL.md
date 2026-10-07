---
name: "gara-keyboard-avoidance"
description: "Corrige formularios web de Gara cuyos inputs o acciones quedan ocultos por el teclado, el viewport móvil o contenedores con scroll; usar cuando el campo activo o su botón no se ven al escribir en móvil."
---

# Teclado y formularios Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe formulario, dispositivo o viewport y reproducción; entrega la corrección del alcance y comprobaciones de foco, scroll y teclado. Si solo hay emulación, informa de ese límite. Al terminar, devuelve lo hecho y espera instrucciones: no encadena otras skills ni hace commit.

Reproduce con los formularios y el layout actuales en navegador móvil. Considera viewport visual, unidades dinámicas, scroll del contenedor, safe areas y foco; es web, no traduzcas patrones de librerías nativas. Mantén visibles el campo activo y sus acciones sin saltos ni listeners duplicados, y restaura el comportamiento al cerrar el teclado. Comprueba orientación, textarea, diálogo, navegación por teclado y escritorio. Con solo emulación de viewport, declara que no se verificó un teclado móvil real.
