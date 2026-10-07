---
name: "gara-fixing-motion-performance"
description: "Diagnostica con medición tirones, saltos de frames o coste de animaciones existentes en la interfaz web de Gara; usar cuando una animación va a trompicones, no para diseñar movimiento nuevo (gara-ui-animation)."
---

# Rendimiento de animación Gara

Lee el [perfil Gara](references/gara.md) y aplica las instrucciones del checkout objetivo.

## Ejecución

Ejecución directa, sin agentes. Recibe la animación, su reproducción y el stack actual; entrega mediciones, diagnóstico y correcciones acotadas. Si faltan herramientas de medida, registra la hipótesis sin presentarla como mejora medida. Aplica los criterios solo al alcance pedido y al sistema existente: sin dependencias nuevas ni rediseño incidental. Al terminar, devuelve el resultado y espera instrucciones; no encadena otras skills ni hace commit.

## Uso

- `/gara-fixing-motion-performance`: aplica estos criterios al trabajo de animación de la conversación.
- `/gara-fixing-motion-performance <archivo>`: revisa el archivo contra las reglas y para cada hallazgo da el fragmento exacto, por qué importa (una frase) y una corrección concreta.

No migres librerías de animación salvo petición expresa; aplica las reglas dentro del stack existente.

## Cuándo aplicar

- Animaciones nuevas o modificadas (CSS, WAAPI, Motion, rAF, GSAP) que se perciben con tirones.
- Movimiento ligado al scroll o revelado al hacer scroll.
- Animación de layout, filtros, máscaras, gradientes o variables CSS.
- Componentes con `will-change`, transforms o mediciones de layout.

## Glosario de pasos de render

- composición: `transform`, `opacity`
- pintado: color, bordes, gradientes, máscaras, imágenes, filtros
- layout: tamaño, posición, flujo, grid, flex

## Prioridad de las reglas

| prioridad | categoría | impacto |
|-----------|-----------|---------|
| 1 | patrones prohibidos | crítico |
| 2 | elegir el mecanismo | crítico |
| 3 | medición | alto |
| 4 | scroll | alto |
| 5 | pintado | medio-alto |
| 6 | capas | medio |
| 7 | blur y filtros | medio |
| 8 | view transitions | bajo |
| 9 | límites de la herramienta | crítico |

### 1. Patrones prohibidos (crítico)

- No intercales lecturas y escrituras de layout en el mismo frame.
- No animes layout de forma continua en superficies grandes o relevantes.
- No dirijas animaciones desde `scrollTop`, `scrollY` ni eventos de scroll.
- Ningún bucle `requestAnimationFrame` sin condición de parada.
- No mezcles varios sistemas de animación que midan o muten layout.

### 2. Elegir el mecanismo (crítico)

- Por defecto, `transform` y `opacity`.
- Animación dirigida por JS solo cuando la interacción lo exija.
- Animar pintado o layout solo en superficies pequeñas y aisladas.
- Un efecto puntual se tolera más que el movimiento continuo.
- Antes de quitar el movimiento, prefiere degradar la técnica.

### 3. Medición (alto)

- Mide una vez y anima con `transform` u `opacity`; agrupa todas las lecturas del DOM antes de las escrituras.
- No leas layout repetidamente durante la animación.
- Para efectos tipo layout, prefiere FLIP.

### 4. Scroll (alto)

- Para movimiento ligado al scroll, prefiere Scroll o View Timelines cuando existan.
- Usa `IntersectionObserver` para visibilidad y para pausar; no consultes la posición de scroll en bucle.
- Pausa o detén las animaciones fuera de pantalla.
- El movimiento ligado al scroll no provoca layout ni pintado continuos en superficies grandes.

### 5. Pintado (medio-alto)

- Animación que provoca pintado solo en elementos pequeños y aislados; nunca propiedades costosas de pintado en contenedores grandes.
- No animes variables CSS que gobiernen transform, opacity o posición, ni variables heredadas; acota las variables animadas localmente.

### 6. Capas (medio)

- La composición exige promoción de capa; no la des por supuesta.
- `will-change` temporal y quirúrgico; evita muchas capas o capas grandes.
- Valida el comportamiento de capas con herramientas cuando el rendimiento importe.

### 7. Blur y filtros (medio)

- Blur pequeño (<= 8px), solo en efectos breves y puntuales; nunca continuo ni en superficies grandes.
- Prefiere opacity y translate antes que blur.

### 8. View transitions (bajo)

- Solo para cambios de navegación; evítalas en UI de interacción intensa o cuando se necesite interrupción o cancelación.
- Un cambio de tamaño puede desencadenar layout.
- Para implementarlas o corregir su comportamiento, la skill adecuada es gara-view-transitions.

### 9. Límites de la herramienta (crítico)

- No migres ni reescribas librerías de animación sin petición expresa; aplica estas reglas dentro del sistema existente.
- Nunca migres una API a medias ni mezcles estilos dentro de un mismo componente.

## Correcciones habituales

```css
/* thrash de layout: anima transform en lugar de width */
/* antes */   .panel { transition: width 0.3s; }
/* después */ .panel { transition: transform 0.3s; }

/* ligado al scroll: usa scroll-timeline en lugar de JS */
/* antes */   window.addEventListener('scroll', () => el.style.opacity = scrollY / 500)
/* después */ .reveal { animation: fade-in linear; animation-timeline: view(); }
```

```js
// medición: agrupa lecturas antes de escrituras (FLIP)
// antes: thrash de layout
el.style.left = el.getBoundingClientRect().left + 10 + 'px';
// después: mide una vez y anima con transform
const first = el.getBoundingClientRect();
el.classList.add('moved');
const last = el.getBoundingClientRect();
el.style.transform = `translateX(${first.left - last.left}px)`;
requestAnimationFrame(() => { el.style.transition = 'transform 0.3s'; el.style.transform = ''; });
```

## Orden de trabajo

Aplica primero las reglas críticas. Elige el trabajo de render más barato que cumpla la intención. Para toda decisión no habitual, indica la restricción que la justifica (tamaño de superficie, duración o necesidad de interacción). Prefiere notas accionables y alternativas concretas a la teoría; una mejora solo es "medida" si hay medición (DevTools Performance, capas, frames).
