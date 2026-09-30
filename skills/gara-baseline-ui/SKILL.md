---
name: "gara-baseline-ui"
description: "Revisa y corrige el acabado de pantallas web de Gara: jerarquía, estados, controles y movimiento, conservando sus tokens y stack actuales."
---

# Acabado de interfaz Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe pantalla/archivo y comportamiento solicitado; entrega hallazgos con ubicación y corrección concreta, o cambios de acabado del alcance. Sin navegador, declara los estados visuales no comprobados. No requiere delegación.

Aplica los criterios al alcance pedido y al sistema visual observado en el checkout. Conserva dependencias, componentes y decisiones vigentes; un problema de acabado no autoriza rediseñar la interfaz.

## Uso y devolución

Usa `$gara-baseline-ui` en Codex o `/gara-baseline-ui` en Claude. Para revisar un archivo o pantalla, aporta ubicación o snippet, fallo observado, consecuencia para el usuario y una corrección concreta. Si se pidió corregir, implementa cambios acotados y describe la comprobación realizada.

## Stack y componentes

- Usa primero los tokens CSS/Tailwind, temas y primitivas existentes de Gara. Los defaults de Tailwind son una alternativa cuando el proyecto no define ese valor, no un motivo para reemplazar tokens actuales.
- Conserva la utilidad de clases vigente; usa `cn` si ya forma parte del código. No añadas `clsx`, `tailwind-merge`, `tw-animate-css`, `motion/react` u otra dependencia como requisito de esta skill.
- Prefiere HTML nativo y las primitivas accesibles ya utilizadas para teclado, foco, diálogos y menús. Mantén un único sistema de primitivas por interacción. Una nueva librería necesita una carencia concreta y un cambio de alcance justificado.
- Los controles tienen nombre accesible; los botones de icono usan `aria-label` o `aria-labelledby`. Conserva foco visible, orden de teclado y restauración del foco al cerrar overlays. Para una revisión específica de accesibilidad, aplica gara-fixing-accessibility si está disponible.

## Interacción y estados

- Usa la confirmación accesible existente para acciones destructivas que la requieran; conserva el foco y la posibilidad de cancelar.
- Muestra estados de carga adecuados al contenido, errores junto a la acción o campo afectado y una acción siguiente clara en estados vacíos.
- Permite pegar en inputs y textareas. No escondas acciones o errores esenciales detrás de hover.
- En superficies móviles de altura completa, usa el viewport dinámico cuando corresponda y respeta `safe-area-inset` en elementos fijos. Comprueba scroll, campos y acciones con teclado; no sustituyas unidades de altura sin revisar su contenedor.

## Movimiento

- Añade movimiento solo si comunica feedback, orientación o continuidad del comportamiento solicitado. Conserva el movimiento útil existente sin introducir decoración incidental.
- Prefiere transiciones CSS para estados interruptibles; usa WAAPI o la infraestructura de animación ya instalada cuando haga falta orquestación. No impongas `motion/react` para animación JavaScript.
- Prioriza `transform` y `opacity`. Anima layout o propiedades que provocan paint solo en superficies pequeñas y aisladas con una necesidad concreta y rendimiento comprobado; evita `transition: all`.
- Usa duraciones y easing de los tokens actuales. Si necesitas definirlos, aplica el contexto y la frecuencia de gara-ui-animation cuando esté disponible: feedback de botón suele estar en 100–160 ms, popovers en 125–200 ms y modales/drawers en 200–350 ms. Son rangos de partida, no límites universales; una acción frecuente debe responder de inmediato y la duración debe corresponder a la distancia y al propósito.
- Toda animación contempla `prefers-reduced-motion: reduce`: elimina desplazamientos, escalado y keyframes no esenciales; conserva el cambio de estado inmediato o un fade discreto. El foco y la operación no dependen de la animación.
- Comprueba interrupción, entradas/salidas rápidas y cambio de tema. Pausa bucles fuera de pantalla; aplica hover animado solo a puntero fino con hover disponible. Evita movimiento pesado de imágenes o superficies grandes.

## Tipografía, layout y color

- Conserva tipografía, espaciados y jerarquía vigentes. Usa números tabulares en datos cuando mejoren su comparación y controla el wrapping de nombres, secuencias e identificadores largos.
- Usa `text-balance`, `text-pretty`, truncado o line-clamp cuando resuelvan un problema de lectura; no ocultes datos científicos esenciales. Conserva el letter-spacing existente salvo una necesidad del encargo.
- Sigue la escala de z-index del proyecto y comprueba las capas de menús, paneles y diálogos. Reutiliza dimensiones y espaciados existentes antes de añadir valores arbitrarios.
- Usa los colores y sombras de tema actuales. Distingue los colores científicos del visor de los acentos decorativos; no introduzcas gradientes, glows o una paleta nueva para resolver un problema de acabado.

## Rendimiento y comprobación

- Evita animar grandes superficies de `blur()` o `backdrop-filter`. Usa `will-change` solo durante movimiento que lo necesite y retíralo después.
- Expresa estado derivado mediante render cuando sea posible; conserva efectos necesarios para sincronizar APIs o sistemas externos.
- Comprueba los flujos afectados en escritorio/móvil, claro/oscuro, teclado, movimiento reducido, carga, vacío y error. Basa afirmaciones de rendimiento en medidas; si no hay navegador o medición disponible, documenta el límite.
