---
name: "gara-baseline-ui"
description: "Revisa y corrige el acabado de una pantalla web de Gara que ya existe: jerarquía, estados, controles, tipografía y movimiento, conservando sus tokens y stack; usar para pulir lo hecho, no para diseñar una pantalla nueva (gara-frontend-design) ni para un problema solo de accesibilidad, animación o metadatos."
---

# Acabado de interfaz Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe pantalla o archivo y el comportamiento solicitado; entrega hallazgos con ubicación y corrección concreta, o cambios de acabado del alcance. Sin navegador, declara los estados visuales no comprobados. Aplica los criterios al alcance pedido y al sistema visual observado: conserva dependencias, componentes y decisiones vigentes; un problema de acabado no autoriza a rediseñar la interfaz. Al terminar, devuelve hallazgos o cambios y las comprobaciones hechas, y espera instrucciones; no encadena otras skills ni hace commit.

## Uso y devolución

`/gara-baseline-ui <archivo o pantalla>`. Para una revisión, aporta ubicación o fragmento, fallo observado, consecuencia para el usuario y corrección concreta. Si se pidió corregir, implementa cambios acotados y describe la comprobación realizada.

Esta skill da una pasada general. Cuando el problema sea específico, indica al usuario la skill que lo cubre en profundidad y no la invoques tú: `/gara-fixing-accessibility` (foco, teclado, contraste, semántica), `/gara-ui-animation` (diseño o medición de movimiento), `/gara-fixing-motion-performance` (tirones) o `/gara-keyboard-avoidance` (campos tapados por el teclado).

## Stack y componentes

- Usa primero los tokens CSS/Tailwind, temas y primitivas existentes de Gara. Los defaults de Tailwind son alternativa cuando el proyecto no define ese valor, no motivo para reemplazar tokens actuales.
- Conserva la utilidad de clases vigente (`cn` si ya se usa). No añadas `clsx`, `tailwind-merge`, `tw-animate-css`, `motion/react` u otra dependencia como requisito de esta skill.
- Prefiere HTML nativo y las primitivas accesibles ya usadas para teclado, foco, diálogos y menús; un único sistema de primitivas por interacción. Una librería nueva necesita una carencia concreta y un cambio de alcance justificado.
- Los controles tienen nombre accesible (los de solo icono, `aria-label`) y conservan foco visible y restauración del foco al cerrar overlays; el detalle es de `gara-fixing-accessibility`.

## Interacción y estados

- Las acciones destructivas usan la confirmación accesible existente, con foco y posibilidad de cancelar.
- Estados de carga adecuados al contenido, errores junto a la acción o campo afectado y una acción siguiente clara en los vacíos.
- Permite pegar en inputs y textareas. No escondas acciones o errores esenciales tras hover.
- En superficies móviles de altura completa, usa el viewport dinámico cuando corresponda y respeta `safe-area-inset` en elementos fijos; no sustituyas unidades de altura sin revisar su contenedor.

## Movimiento

- Solo si comunica feedback, orientación o continuidad. Conserva el movimiento útil existente; sin decoración incidental.
- Prefiere transiciones CSS para estados interruptibles; WAAPI o la infraestructura de animación ya instalada para orquestar. No impongas `motion/react`.
- `transform` y `opacity` primero; nada de `transition: all`. Layout o pintado animados solo en superficies pequeñas y aisladas con necesidad y rendimiento comprobados.
- Duraciones y easing de los tokens actuales; si hay que definirlos, usa los rangos de `gara-ui-animation` (feedback de botón, popovers, modales) como punto de partida, no como límite.
- Toda animación contempla `prefers-reduced-motion: reduce`; foco y operación no dependen de ella. Comprueba interrupción, entradas/salidas rápidas y cambio de tema; pausa bucles fuera de pantalla y limita el hover animado a puntero fino.

## Tipografía, layout y color

- Conserva tipografía, espaciados y jerarquía vigentes. Números tabulares en datos comparables y control del wrapping de nombres, secuencias e identificadores largos.
- `text-balance`, `text-pretty`, truncado o line-clamp solo si resuelven un problema de lectura; no ocultes datos científicos esenciales. Conserva el letter-spacing salvo necesidad del encargo.
- Sigue la escala de z-index del proyecto y comprueba capas de menús, paneles y diálogos. Reutiliza dimensiones y espaciados existentes antes de añadir valores arbitrarios.
- Colores y sombras de tema actuales. Distingue los colores científicos del visor de los acentos decorativos; sin gradientes, glows ni paleta nueva para resolver un problema de acabado.

## Rendimiento y comprobación

- No animes superficies grandes con `blur()` o `backdrop-filter`. `will-change` solo durante el movimiento que lo necesite.
- Expresa el estado derivado mediante render cuando sea posible; conserva los efectos necesarios para sincronizar APIs o sistemas externos.
- Comprueba los flujos afectados en escritorio/móvil, claro/oscuro, teclado, movimiento reducido, carga, vacío y error. Las afirmaciones de rendimiento se basan en medidas; sin navegador o medición, documenta el límite.
