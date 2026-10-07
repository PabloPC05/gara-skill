---
name: "gara-theme-switcher"
description: "Implementa o corrige el cambio de tema (claro, oscuro, sistema) de la interfaz web de Gara, con su proveedor de tema y tokens actuales; usar cuando falle o se pida el selector, la persistencia o la sincronización del tema."
---

# Temas de interfaz Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe el comportamiento esperado, el mecanismo de tema y los tokens actuales; entrega cambios de tema/persistencia y pruebas pertinentes. Si falta navegador, declara las transiciones y la persistencia no comprobadas. Al terminar, devuelve lo hecho y espera instrucciones: no encadena otras skills ni hace commit.

Inspecciona el proveedor de tema (`ThemeProvider` o equivalente vigente), la persistencia de la preferencia y la clase `dark` real. Reutiliza claro, oscuro y sistema; no añadas un segundo proveedor ni traslades recetas de otras plataformas (es una SPA web). Comprueba la sincronización con el tema del sistema, la carga inicial y el contraste de paneles, controles y visor. Una revelación animada es opcional y respeta reduced motion; la operación y el foco no dependen de ella (para diseñarla, `/gara-ui-animation`). Prueba temas y persistencia en navegador con aceptación pertinente.
