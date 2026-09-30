---
name: "gara-theme-switcher"
description: "Implementa o corrige cambios de tema en la interfaz web de Gara, usando ThemeProvider y los tokens actuales."
---

# Temas de interfaz Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe comportamiento esperado, ThemeProvider y tokens actuales; entrega cambios de tema/persistencia y pruebas pertinentes. Si falta navegador, declara las transiciones y persistencia no comprobadas. No requiere delegación.

Inspecciona ThemeProvider, persistencia de preferencia y la clase dark real. Reutiliza light, dark y system; no añadas un segundo proveedor o una receta de Kotlin/React Native. Comprueba sincronización con el tema del sistema, carga inicial y contraste de paneles, controles y visor. Una revelación animada es opcional y sigue reduced motion; la operación y el foco no dependen de ella. Prueba temas y persistencia en navegador con aceptación pertinente.
