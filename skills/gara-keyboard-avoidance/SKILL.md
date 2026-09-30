---
name: "gara-keyboard-avoidance"
description: "Corrige formularios web de Gara cuyos inputs o acciones quedan ocultos por el teclado, viewport móvil o contenedores con scroll."
---

# Teclado y formularios Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe formulario, dispositivo/viewport y reproducción; entrega corrección del alcance y comprobaciones de foco, scroll y teclado. Si solo hay emulación, informa ese límite. No requiere delegación.

Reproduce con los formularios y layout actuales en navegador móvil. Considera viewport visual, unidades dinámicas, scroll del contenedor, safe areas y foco; no traduzcas KeyboardAvoidingView literalmente a React web. Mantén visibles campo activo y acciones sin saltos ni listeners duplicados, y restaura el comportamiento al cerrar teclado. Comprueba orientación, textarea, diálogo, navegación por teclado y escritorio. Si solo hay emulación de viewport, declara que no se verificó un teclado físico móvil.
