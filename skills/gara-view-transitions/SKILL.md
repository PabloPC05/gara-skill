---
name: "gara-view-transitions"
description: "Implementa o corrige transiciones entre vistas de la SPA de Gara respetando sus paneles, pestañas y diálogos existentes."
---

# Transiciones de vistas Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe navegación, estados y transición requerida; entrega cambios con validación de foco, cancelación y contexto. Si falta una API, degrada al cambio inmediato y registra lo comprobado. No requiere delegación.

Identifica el mecanismo real de navegación antes de modificarlo. No instales Expo Router, un native stack ni un router nuevo para animar paneles existentes. Decide qué transición comunica un cambio real y evita animar el render molecular sin necesidad. Coordina entrada/salida, foco, estado y cancelación ante cambios rápidos. Respeta reduced motion y degrada a un cambio inmediato cuando una API no esté disponible. Prueba navegación repetida, cierres, errores y persistencia del contexto del visor.
