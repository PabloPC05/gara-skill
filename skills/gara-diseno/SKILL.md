---
name: "gara-diseno"
description: "Usar cuando el usuario pida documentar o definir el sistema visual de Gara (tipografía, colores por tema, espaciados, estados) en DISENO.md a partir de su código. No implementa pantallas (gara-frontend-design) ni corrige acabado (gara-baseline-ui)."
disable-model-invocation: true
---

# Diseño Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Directa, sin agentes.

1. Lee el CSS, Tailwind, `ThemeProvider` y los componentes actuales. Documenta lo observado en Gara; no impongas una paleta o un estilo ajenos.
2. Escribe `DISENO.md` con tipografía (Lato y sus fallbacks reales), colores por tema, espaciados medibles, foco, estados y movimiento reducido. Mantén los colores científicos de Molstar separados de los decorativos.
3. Distingue siempre valores existentes (con su origen en el código) de propuestas nuevas. Si falta una pantalla o documentación, deriva solo lo comprobable y registra el límite.
4. Pregunta solo decisiones visuales materiales. La ruta de `DISENO.md` es la que indique el usuario; si no la da, propón una antes de escribir.

## Parada

Solo escribes `DISENO.md`: no cambies código ni estilos de la interfaz. Devuelve la ruta, lo documentado, las propuestas y las decisiones pendientes, y espera al usuario.
