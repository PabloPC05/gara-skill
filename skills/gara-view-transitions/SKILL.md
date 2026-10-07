---
name: "gara-view-transitions"
description: "Implementa o corrige transiciones al cambiar de vista en la SPA de Gara (paneles, pestañas, diálogos), con su mecanismo de navegación actual; usar cuando el cambio de vista salte, pierda foco o se pida animarlo."
---

# Transiciones de vistas Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe navegación, estados y la transición requerida; entrega cambios con validación de foco, cancelación y contexto. Si falta una API, degrada al cambio inmediato y registra lo comprobado. Al terminar, devuelve lo hecho y espera instrucciones: no encadena otras skills ni hace commit.

Identifica el mecanismo real de navegación antes de modificarlo; no instales un router ni librerías nuevas solo para animar paneles existentes. Decide qué transición comunica un cambio real y evita animar el render molecular sin necesidad. Coordina entrada/salida, foco, estado y cancelación ante cambios rápidos. Respeta reduced motion y degrada a un cambio inmediato cuando una API no esté disponible. Prueba navegación repetida, cierres, errores y persistencia del contexto del visor. Para la curva y la duración, `/gara-ui-animation`; si hay tirones, `/gara-fixing-motion-performance`.
